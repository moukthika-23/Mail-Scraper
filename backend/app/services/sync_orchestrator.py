from __future__ import annotations

import asyncio
import json
from typing import Optional

from app.core.config import settings
from app.core.db import supabase
from app.services.gmail_sync_service import sync_gmail_messages

_scheduled_users: set[str] = set()
_lock = asyncio.Lock()


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


def _fetch_sync_state_row(user_id: str) -> Optional[dict]:
    response = supabase.table("sync_state").select("*").eq("user_id", user_id).limit(1).execute()
    rows = response.data or []
    return rows[0] if rows else None


def _is_backfill_pending(row: Optional[dict]) -> bool:
    if not row:
        return False
    if row.get("status") == "syncing":
        return True
    meta = _decode_sync_meta(row.get("history_id"))
    return bool(meta) and meta.get("backfill_complete") is False


async def _auto_backfill_worker(user_id: str, initial_delay_seconds: int) -> None:
    try:
        if initial_delay_seconds > 0:
            await asyncio.sleep(initial_delay_seconds)

        while True:
            row = _fetch_sync_state_row(user_id)
            if not row:
                return

            status = row.get("status")
            meta = _decode_sync_meta(row.get("history_id"))
            if meta.get("backfill_complete") is True:
                return

            if status == "syncing":
                await asyncio.sleep(max(1, settings.GMAIL_AUTO_BACKFILL_INTERVAL_SECONDS))
                continue

            if status not in {"done", "error", "idle"}:
                return

            await sync_gmail_messages(
                user_id,
                mode="smart",
                date_from=meta.get("requested_from"),
                date_to=meta.get("requested_to"),
            )

            updated_row = _fetch_sync_state_row(user_id)
            updated_meta = _decode_sync_meta((updated_row or {}).get("history_id"))
            if updated_meta.get("backfill_complete") is True:
                return

            await asyncio.sleep(max(1, settings.GMAIL_AUTO_BACKFILL_INTERVAL_SECONDS))
    finally:
        async with _lock:
            _scheduled_users.discard(user_id)


async def schedule_auto_backfill(user_id: str, *, delay_seconds: Optional[int] = None) -> bool:
    if not settings.GMAIL_AUTO_BACKFILL_ENABLED:
        return False

    if delay_seconds is None:
        delay_seconds = settings.GMAIL_AUTO_BACKFILL_INITIAL_DELAY_SECONDS

    row = _fetch_sync_state_row(user_id)
    if not _is_backfill_pending(row):
        return False

    async with _lock:
        if user_id in _scheduled_users:
            return False
        _scheduled_users.add(user_id)

    asyncio.create_task(_auto_backfill_worker(user_id, max(0, delay_seconds)))
    return True


async def resume_auto_backfills_from_db() -> int:
    if not settings.GMAIL_AUTO_BACKFILL_ENABLED:
        return 0

    response = supabase.table("sync_state").select("user_id,status,history_id").limit(1000).execute()
    rows = response.data or []
    resumed = 0
    for row in rows:
        user_id = row.get("user_id")
        if not user_id:
            continue
        if _is_backfill_pending(row):
            created = await schedule_auto_backfill(user_id, delay_seconds=5)
            if created:
                resumed += 1
    return resumed
