from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.db import supabase
from app.core.security import get_current_user_id

router = APIRouter()


class SaveQueryRequest(BaseModel):
    name: str
    query_text: str
    chart_spec_json: dict[str, Any]


class SavedQuery(BaseModel):
    id: str
    name: str
    query_text: str
    chart_spec_json: dict[str, Any]
    created_at: str


@router.get("", response_model=list[SavedQuery])
async def list_queries(user_id: str = Depends(get_current_user_id)):
    response = (
        supabase.table("custom_queries")
        .select("id,name,query_text,chart_spec_json,created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    rows = response.data or []
    return [
        SavedQuery(
            id=str(row.get("id")),
            name=row.get("name") or "",
            query_text=row.get("query_text") or "",
            chart_spec_json=row.get("chart_spec_json") or {},
            created_at=str(row.get("created_at") or ""),
        )
        for row in rows
    ]


@router.post("", response_model=SavedQuery, status_code=201)
async def save_query(req: SaveQueryRequest, user_id: str = Depends(get_current_user_id)):
    payload = {
        "user_id": user_id,
        "name": req.name,
        "query_text": req.query_text,
        "chart_spec_json": req.chart_spec_json,
    }

    response = (
        supabase.table("custom_queries")
        .insert(payload)
        .select("id,name,query_text,chart_spec_json,created_at")
        .execute()
    )
    row = (response.data or [None])[0]
    if not row:
        raise HTTPException(
            status_code=502,
            detail="Query saved, but the database did not return the persisted record.",
        )

    return SavedQuery(
        id=str(row.get("id") or ""),
        name=row.get("name") or req.name,
        query_text=row.get("query_text") or req.query_text,
        chart_spec_json=row.get("chart_spec_json") or req.chart_spec_json,
        created_at=str(row.get("created_at") or datetime.now(timezone.utc).isoformat()),
    )
