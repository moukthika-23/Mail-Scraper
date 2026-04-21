from __future__ import annotations

import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional

from app.core.db import supabase
from app.core.security import get_current_user_id
from app.services.gmail_sync_service import sync_gmail_messages
from app.services.sync_orchestrator import schedule_auto_backfill

router = APIRouter()


class SyncRequest(BaseModel):
    mode: Literal["full", "incremental", "smart"] = "smart"
    date_from: Optional[str] = None
    date_to: Optional[str] = None


class SyncStatus(BaseModel):
    status: str
    emails_total: int
    emails_synced: int
    last_synced_at: Optional[str]
    history_id: Optional[str] = None
    phase: Optional[str] = None
    detail: Optional[str] = None
    oldest_synced_at: Optional[str] = None
    backfill_complete: Optional[bool] = None
    backfill_cursor_end: Optional[str] = None


def _first_row(response) -> Optional[dict]:
    data = getattr(response, "data", None) or []
    return data[0] if data else None


def _decode_sync_meta(raw_history_id: Optional[str]) -> dict:
    if not raw_history_id:
        return {}
    try:
        parsed = json.loads(raw_history_id)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"history_id": raw_history_id}


async def _run_sync_task(user_id: str, req: SyncRequest) -> None:
    try:
        await sync_gmail_messages(user_id, mode=req.mode, date_from=req.date_from, date_to=req.date_to)
        if req.mode == "smart":
            await schedule_auto_backfill(user_id)
    except Exception as exc:
        print(f"[Gmail Sync] Background task failed for user {user_id}: {exc}")


@router.post("/start", summary="Trigger Gmail sync")
async def start_sync(
    req: SyncRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
):
    """Starts Gmail ingestion for the authenticated user."""
    existing = (
        supabase.table("sync_state")
        .select("status")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    existing_row = _first_row(existing)
    if existing_row and existing_row.get("status") == "syncing":
        return {"task_id": f"sync-{user_id}", "mode": req.mode, "status": "already_syncing"}

    supabase.table("sync_state").upsert(
        {
            "user_id": user_id,
            "status": "syncing",
            "emails_total": 0,
            "emails_synced": 0,
        },
        on_conflict="user_id",
    ).execute()

    background_tasks.add_task(_run_sync_task, user_id, req)
    return {"task_id": f"sync-{user_id}", "mode": req.mode, "status": "queued"}


@router.get("/status", summary="Poll sync progress (SSE)")
async def sync_status(user_id: str = Depends(get_current_user_id)):
    """Returns current sync state from the database."""
    response = (
        supabase.table("sync_state")
        .select("status,emails_total,emails_synced,last_synced_at,history_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    sync_row = _first_row(response)
    if not sync_row:
        return SyncStatus(status="idle", emails_total=0, emails_synced=0, last_synced_at=None)

    status = sync_row.get("status", "idle")
    if status not in {"idle", "syncing", "done", "error"}:
        raise HTTPException(status_code=500, detail="Invalid sync status in database")

    sync_meta = _decode_sync_meta(sync_row.get("history_id"))

    return SyncStatus(
        status=status,
        emails_total=sync_row.get("emails_total") or 0,
        emails_synced=sync_row.get("emails_synced") or 0,
        last_synced_at=sync_row.get("last_synced_at"),
        history_id=sync_meta.get("history_id"),
        phase=sync_meta.get("phase"),
        detail=sync_meta.get("detail"),
        oldest_synced_at=sync_meta.get("oldest_synced_at"),
        backfill_complete=sync_meta.get("backfill_complete"),
        backfill_cursor_end=sync_meta.get("backfill_cursor_end"),
    )
