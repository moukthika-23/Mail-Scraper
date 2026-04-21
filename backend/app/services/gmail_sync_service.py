from __future__ import annotations

import asyncio
import base64
import email.utils
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.db import supabase
from app.core.security import decrypt_token

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _headers_by_name(headers: Optional[List[Dict[str, str]]]) -> Dict[str, str]:
    return {h.get("name", "").lower(): h.get("value", "") for h in headers or []}


def _parse_sender(raw_from: str) -> tuple[str, str]:
    name, address = email.utils.parseaddr(raw_from or "")
    return address.lower(), name or address


def _parse_gmail_date(raw_date: Optional[str], internal_date: Optional[str]) -> Optional[str]:
    if raw_date:
        try:
            parsed = email.utils.parsedate_to_datetime(raw_date)
            if parsed:
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc).isoformat()
        except (TypeError, ValueError, IndexError):
            pass

    if internal_date:
        return datetime.fromtimestamp(int(internal_date) / 1000, tz=timezone.utc).isoformat()

    return None


def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_iso_date(value: Optional[str]) -> Optional[date]:
    parsed = _parse_iso_datetime(value)
    if parsed:
        return parsed.date()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _date_to_str(value: date) -> str:
    return value.isoformat()


def _decode_body_data(data: Optional[str]) -> str:
    if not data:
        return ""
    padded = data + ("=" * (-len(data) % 4))
    decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return decoded.decode("utf-8", errors="replace")


def _strip_html(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value)
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _extract_body(payload: Optional[Dict[str, Any]]) -> str:
    if not payload:
        return ""

    text_chunks: list[str] = []
    html_chunks: list[str] = []

    def walk(part: dict[str, Any]) -> None:
        mime_type = part.get("mimeType", "")
        body_data = part.get("body", {}).get("data")
        if body_data and mime_type == "text/plain":
            text_chunks.append(_decode_body_data(body_data))
        elif body_data and mime_type == "text/html":
            html_chunks.append(_strip_html(_decode_body_data(body_data)))

        for child in part.get("parts", []) or []:
            walk(child)

    walk(payload)
    body = "\n".join(chunk.strip() for chunk in text_chunks if chunk.strip())
    if body:
        return body
    return "\n".join(chunk for chunk in html_chunks if chunk)


def _gmail_query(date_from: Optional[date], date_to: Optional[date]) -> Optional[str]:
    parts: list[str] = []
    if date_from:
        inclusive_after = (date_from - timedelta(days=1)).strftime("%Y/%m/%d")
        parts.append(f"after:{inclusive_after}")
    if date_to:
        inclusive_before = (date_to + timedelta(days=1)).strftime("%Y/%m/%d")
        parts.append(f"before:{inclusive_before}")
    return " ".join(parts) or None


def _decode_sync_meta(raw_history_id: Optional[str]) -> dict[str, Any]:
    if not raw_history_id:
        return {}
    try:
        parsed = json.loads(raw_history_id)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"history_id": raw_history_id}


def _encode_sync_meta(meta: dict[str, Any]) -> str:
    compact: dict[str, Any] = {}
    for key, value in meta.items():
        if value is None:
            continue
        compact[key] = value
    return json.dumps(compact, separators=(",", ":"))


def _fetch_sync_state_row(user_id: str) -> Optional[dict[str, Any]]:
    response = supabase.table("sync_state").select("*").eq("user_id", user_id).limit(1).execute()
    data = response.data or []
    return data[0] if data else None


def _set_sync_state(
    user_id: str,
    *,
    status: str,
    emails_total: Optional[int] = None,
    emails_synced: Optional[int] = None,
    history_id: Optional[str] = None,
    last_synced_at: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> None:
    record: dict[str, Any] = {
        "user_id": user_id,
        "status": status,
    }
    if emails_total is not None:
        record["emails_total"] = emails_total
    if emails_synced is not None:
        record["emails_synced"] = emails_synced
    if meta is not None:
        payload = dict(meta)
        if history_id is not None:
            payload["history_id"] = history_id
        record["history_id"] = _encode_sync_meta(payload)
    elif history_id is not None:
        record["history_id"] = history_id
    if last_synced_at is not None:
        record["last_synced_at"] = last_synced_at

    supabase.table("sync_state").upsert(record, on_conflict="user_id").execute()


def _fetch_user(user_id: str) -> dict[str, Any]:
    response = supabase.table("users").select("*").eq("id", user_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    return response.data


def _fetch_email_date_bounds(user_id: str) -> tuple[Optional[date], Optional[date]]:
    oldest_response = (
        supabase.table("emails")
        .select("date")
        .eq("user_id", user_id)
        .order("date")
        .limit(1)
        .execute()
    )
    latest_response = (
        supabase.table("emails")
        .select("date")
        .eq("user_id", user_id)
        .order("date", desc=True)
        .limit(1)
        .execute()
    )
    oldest = _parse_iso_date((oldest_response.data or [{}])[0].get("date")) if oldest_response.data else None
    latest = _parse_iso_date((latest_response.data or [{}])[0].get("date")) if latest_response.data else None
    return oldest, latest


def _count_indexed_emails(user_id: str) -> int:
    response = supabase.table("emails").select("id", count="exact").eq("user_id", user_id).limit(1).execute()
    return int(getattr(response, "count", 0) or 0)


def _merge_oldest_synced_at(current_value: Optional[str], email_rows: list[dict[str, Any]]) -> Optional[str]:
    candidate_dates = [
        _parse_iso_datetime(row.get("date"))
        for row in email_rows
        if row.get("date")
    ]
    batch_oldest = min((dt for dt in candidate_dates if dt is not None), default=None)
    current_oldest = _parse_iso_datetime(current_value)

    if current_oldest and batch_oldest:
        return min(current_oldest, batch_oldest).isoformat()
    if batch_oldest:
        return batch_oldest.isoformat()
    if current_oldest:
        return current_oldest.isoformat()
    return None


def _phase_message(phase: str, window_start: date, window_end: date) -> str:
    if phase == "recent":
        return f"Syncing recent mail from {_date_to_str(window_start)} to {_date_to_str(window_end)}"
    if phase == "backfill":
        return f"Backfilling older mail from {_date_to_str(window_start)} to {_date_to_str(window_end)}"
    return f"Syncing updates from {_date_to_str(window_start)} to {_date_to_str(window_end)}"


def _window_start(window_end: date, lower_bound: date) -> date:
    span_days = max(1, settings.GMAIL_BACKFILL_WINDOW_DAYS)
    return max(lower_bound, window_end - timedelta(days=span_days - 1))


def _page_size() -> int:
    return max(1, min(settings.GMAIL_PAGE_SIZE, 500))


def _initial_meta(
    mode: str,
    *,
    requested_from: Optional[date],
    requested_to: date,
    backfill_complete: bool,
    oldest_synced_at: Optional[str],
    history_id: Optional[str],
) -> dict[str, Any]:
    return {
        "mode": mode,
        "phase": "idle",
        "requested_from": _date_to_str(requested_from) if requested_from else None,
        "requested_to": _date_to_str(requested_to),
        "backfill_complete": backfill_complete,
        "backfill_cursor_end": None,
        "oldest_synced_at": oldest_synced_at,
        "history_id": history_id,
        "detail": None,
    }


async def _refresh_access_token(refresh_token: str) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=401, detail={"google_token_error": response.json()})
    token_data = response.json()
    return token_data["access_token"]


async def _gmail_get(
    client: httpx.AsyncClient,
    path: str,
    access_token: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    response = await client.get(
        f"{GMAIL_API_BASE}/{path}",
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
    )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail={"gmail_error": response.json()})
    return response.json()


async def _fetch_message_detail(
    client: httpx.AsyncClient,
    access_token: str,
    message: dict[str, str],
    semaphore: asyncio.Semaphore,
) -> Optional[Dict[str, Any]]:
    gmail_id = message["id"]
    params: dict[str, Any] = {
        "format": "full" if settings.GMAIL_SYNC_FULL_BODY else "metadata",
        "metadataHeaders": ["Subject", "From", "Date"],
    }

    async with semaphore:
        try:
            return await _gmail_get(client, f"messages/{gmail_id}", access_token, params)
        except HTTPException as exc:
            print(f"[Gmail Sync] Skipping message {gmail_id}: {exc.detail}")
            return None


def _email_row_from_detail(user_id: str, detail: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], Optional[str]]:
    headers = _headers_by_name(detail.get("payload", {}).get("headers"))
    sender_email, sender_name = _parse_sender(headers.get("from", ""))
    label_ids = detail.get("labelIds", []) or []
    snippet = detail.get("snippet", "")
    body_text = _extract_body(detail.get("payload")) if settings.GMAIL_SYNC_FULL_BODY else snippet

    return (
        {
            "user_id": user_id,
            "gmail_id": detail["id"],
            "thread_id": detail.get("threadId"),
            "subject": headers.get("subject", ""),
            "sender_email": sender_email,
            "sender_name": sender_name,
            "body_text": body_text,
            "snippet": snippet,
            "date": _parse_gmail_date(headers.get("date"), detail.get("internalDate")),
            "is_read": "UNREAD" not in label_ids,
            "is_starred": "STARRED" in label_ids,
            "raw_size_bytes": detail.get("sizeEstimate", 0),
        },
        label_ids,
        detail.get("historyId"),
    )


def _upsert_labels(user_id: str, gmail_label_ids: set[str]) -> dict[str, str]:
    if not gmail_label_ids:
        return {}

    rows = [
        {
            "user_id": user_id,
            "gmail_label_id": label_id,
            "name": label_id,
            "type": "system" if label_id.isupper() else "user",
        }
        for label_id in sorted(gmail_label_ids)
    ]
    supabase.table("labels").upsert(rows, on_conflict="user_id,gmail_label_id").execute()
    label_response = (
        supabase.table("labels")
        .select("id,gmail_label_id")
        .eq("user_id", user_id)
        .in_("gmail_label_id", list(gmail_label_ids))
        .execute()
    )
    return {row["gmail_label_id"]: row["id"] for row in label_response.data or []}


def _refresh_threads(user_id: str, gmail_thread_ids: set[str]) -> None:
    if not gmail_thread_ids:
        return

    response = (
        supabase.table("emails")
        .select("thread_id,subject,date")
        .eq("user_id", user_id)
        .in_("thread_id", list(gmail_thread_ids))
        .limit(10000)
        .execute()
    )
    rows = response.data or []
    by_thread: dict[str, dict[str, Any]] = {}
    for row in rows:
        thread_id = row.get("thread_id")
        if not thread_id:
            continue
        current = by_thread.get(thread_id)
        row_date = row.get("date") or ""
        if not current:
            by_thread[thread_id] = {
                "user_id": user_id,
                "gmail_thread_id": thread_id,
                "subject": row.get("subject"),
                "last_date": row.get("date"),
                "message_count": 1,
            }
            continue
        current["message_count"] += 1
        if row_date > (current.get("last_date") or ""):
            current["last_date"] = row.get("date")
            current["subject"] = row.get("subject") or current.get("subject")

    if by_thread:
        supabase.table("threads").upsert(list(by_thread.values()), on_conflict="user_id,gmail_thread_id").execute()


def _refresh_senders(user_id: str, sender_emails: set[str]) -> None:
    if not sender_emails:
        return

    response = (
        supabase.table("emails")
        .select("sender_email,sender_name,date")
        .eq("user_id", user_id)
        .in_("sender_email", list(sender_emails))
        .limit(10000)
        .execute()
    )
    rows = response.data or []
    grouped: dict[str, dict[str, Any]] = {}
    counts = Counter(row.get("sender_email") for row in rows if row.get("sender_email"))

    for row in rows:
        sender_email = row.get("sender_email")
        if not sender_email or sender_email in grouped:
            continue
        sender_dates = [item.get("date") for item in rows if item.get("sender_email") == sender_email and item.get("date")]
        grouped[sender_email] = {
            "user_id": user_id,
            "email": sender_email,
            "name": row.get("sender_name"),
            "domain": sender_email.split("@")[-1] if "@" in sender_email else "",
            "first_seen": min(sender_dates) if sender_dates else row.get("date"),
            "last_seen": max(sender_dates) if sender_dates else row.get("date"),
            "total_count": counts[sender_email],
        }

    if grouped:
        supabase.table("senders").upsert(list(grouped.values()), on_conflict="user_id,email").execute()


def _upsert_email_labels(
    label_ids_by_gmail_id: dict[str, str],
    email_rows: list[dict[str, Any]],
    labels_by_message: dict[str, list[str]],
) -> None:
    gmail_ids = [row["gmail_id"] for row in email_rows]
    if not gmail_ids:
        return

    email_response = (
        supabase.table("emails")
        .select("id,gmail_id")
        .eq("user_id", email_rows[0]["user_id"])
        .in_("gmail_id", gmail_ids)
        .execute()
    )
    email_ids_by_gmail_id = {row["gmail_id"]: row["id"] for row in email_response.data or []}

    joins = []
    for gmail_id, gmail_label_ids in labels_by_message.items():
        email_id = email_ids_by_gmail_id.get(gmail_id)
        if not email_id:
            continue
        for gmail_label_id in gmail_label_ids:
            label_id = label_ids_by_gmail_id.get(gmail_label_id)
            if label_id:
                joins.append({"email_id": email_id, "label_id": label_id})

    if joins:
        supabase.table("email_labels").upsert(joins, on_conflict="email_id,label_id").execute()


def _upsert_email_batch(
    user_id: str,
    email_rows: list[dict[str, Any]],
    labels_by_message: dict[str, list[str]],
    gmail_label_ids: set[str],
) -> None:
    if not email_rows:
        return

    supabase.table("emails").upsert(email_rows, on_conflict="user_id,gmail_id").execute()
    label_ids_by_gmail_id = _upsert_labels(user_id, gmail_label_ids)
    _upsert_email_labels(label_ids_by_gmail_id, email_rows, labels_by_message)
    _refresh_threads(user_id, {row["thread_id"] for row in email_rows if row.get("thread_id")})
    _refresh_senders(user_id, {row["sender_email"] for row in email_rows if row.get("sender_email")})


async def _sync_message_page(
    user_id: str,
    client: httpx.AsyncClient,
    access_token: str,
    messages: list[dict[str, str]],
    *,
    total_estimate: int,
    synced_so_far: int,
    sync_meta: dict[str, Any],
) -> tuple[int, Optional[str], Optional[str]]:
    all_label_ids: set[str] = set()
    labels_by_message: dict[str, list[str]] = {}
    email_rows: list[dict[str, Any]] = []
    latest_history_id = sync_meta.get("history_id")

    semaphore = asyncio.Semaphore(max(1, settings.GMAIL_CONCURRENCY))
    detail_tasks = [
        _fetch_message_detail(client, access_token, message, semaphore)
        for message in messages
    ]

    processed = 0
    for detail_future in asyncio.as_completed(detail_tasks):
        detail = await detail_future
        processed += 1

        if detail:
            email_row, label_ids, history_id = _email_row_from_detail(user_id, detail)
            email_rows.append(email_row)
            all_label_ids.update(label_ids)
            labels_by_message[email_row["gmail_id"]] = label_ids
            latest_history_id = history_id or latest_history_id

        if processed % 25 == 0 or processed == len(messages):
            _set_sync_state(
                user_id,
                status="syncing",
                emails_total=total_estimate,
                emails_synced=min(total_estimate, synced_so_far + processed),
                history_id=latest_history_id,
                meta=sync_meta,
            )

    if email_rows:
        _upsert_email_batch(user_id, email_rows, labels_by_message, all_label_ids)

    oldest_synced_at = _merge_oldest_synced_at(sync_meta.get("oldest_synced_at"), email_rows)
    return processed, latest_history_id, oldest_synced_at


async def _sync_window(
    user_id: str,
    client: httpx.AsyncClient,
    access_token: str,
    *,
    window_start: date,
    window_end: date,
    phase: str,
    sync_meta: dict[str, Any],
) -> dict[str, Any]:
    query = _gmail_query(window_start, window_end)
    page_token: Optional[str] = None
    total_estimate = 0
    synced_in_window = 0
    latest_history_id = sync_meta.get("history_id")
    oldest_synced_at = sync_meta.get("oldest_synced_at")

    while True:
        meta_for_page = {
            **sync_meta,
            "phase": phase,
            "detail": _phase_message(phase, window_start, window_end),
            "window_start": _date_to_str(window_start),
            "window_end": _date_to_str(window_end),
            "backfill_complete": False,
            "oldest_synced_at": oldest_synced_at,
            "history_id": latest_history_id,
        }
        _set_sync_state(
            user_id,
            status="syncing",
            emails_total=max(total_estimate, synced_in_window),
            emails_synced=synced_in_window,
            history_id=latest_history_id,
            meta=meta_for_page,
        )

        params: dict[str, Any] = {"maxResults": _page_size()}
        if query:
            params["q"] = query
        if page_token:
            params["pageToken"] = page_token

        page = await _gmail_get(client, "messages", access_token, params)
        messages = page.get("messages", []) or []
        total_estimate = max(total_estimate, page.get("resultSizeEstimate", 0), synced_in_window + len(messages))

        if not messages:
            break

        processed, latest_history_id, oldest_synced_at = await _sync_message_page(
            user_id,
            client,
            access_token,
            messages,
            total_estimate=total_estimate,
            synced_so_far=synced_in_window,
            sync_meta=meta_for_page,
        )
        synced_in_window += processed
        page_token = page.get("nextPageToken")

        meta_after_page = {
            **meta_for_page,
            "oldest_synced_at": oldest_synced_at,
            "history_id": latest_history_id,
        }
        _set_sync_state(
            user_id,
            status="syncing",
            emails_total=total_estimate,
            emails_synced=min(total_estimate, synced_in_window),
            history_id=latest_history_id,
            meta=meta_after_page,
        )

        if not page_token:
            break

    return {
        "history_id": latest_history_id,
        "oldest_synced_at": oldest_synced_at,
        "emails_total": total_estimate,
        "emails_synced": synced_in_window,
    }


async def _sync_range_windowed(
    user_id: str,
    client: httpx.AsyncClient,
    access_token: str,
    *,
    start_date: date,
    end_date: date,
    phase: str,
    sync_meta: dict[str, Any],
) -> dict[str, Any]:
    if start_date > end_date:
        return {"history_id": sync_meta.get("history_id"), "oldest_synced_at": sync_meta.get("oldest_synced_at")}

    cursor_end = end_date
    latest_history_id = sync_meta.get("history_id")
    oldest_synced_at = sync_meta.get("oldest_synced_at")
    last_window_total = 0
    last_window_synced = 0

    while cursor_end >= start_date:
        current_start = _window_start(cursor_end, start_date)
        window_result = await _sync_window(
            user_id,
            client,
            access_token,
            window_start=current_start,
            window_end=cursor_end,
            phase=phase,
            sync_meta={
                **sync_meta,
                "history_id": latest_history_id,
                "oldest_synced_at": oldest_synced_at,
            },
        )
        latest_history_id = window_result.get("history_id") or latest_history_id
        oldest_synced_at = window_result.get("oldest_synced_at") or oldest_synced_at
        last_window_total = int(window_result.get("emails_total") or last_window_total)
        last_window_synced = int(window_result.get("emails_synced") or last_window_synced)
        cursor_end = current_start - timedelta(days=1)

    return {
        "history_id": latest_history_id,
        "oldest_synced_at": oldest_synced_at,
        "emails_total": last_window_total,
        "emails_synced": last_window_synced,
    }


def _requested_range(date_from: Optional[str], date_to: Optional[str]) -> tuple[Optional[date], date]:
    today = datetime.now(timezone.utc).date()
    requested_to = _parse_iso_date(date_to) or today
    requested_from = _parse_iso_date(date_from)
    if requested_from and requested_from > requested_to:
        raise HTTPException(status_code=400, detail="date_from must be before or equal to date_to")
    return requested_from, requested_to


async def sync_gmail_messages(
    user_id: str,
    *,
    mode: str = "smart",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> Dict[str, Any]:
    user = _fetch_user(user_id)
    refresh_token_enc = user.get("refresh_token_enc")
    if not refresh_token_enc:
        raise HTTPException(status_code=409, detail="Google refresh token missing. Reconnect Gmail.")

    requested_from, requested_to = _requested_range(date_from, date_to)
    existing_sync_row = _fetch_sync_state_row(user_id)
    existing_meta = _decode_sync_meta(existing_sync_row.get("history_id")) if existing_sync_row else {}
    existing_history_id = existing_meta.get("history_id")
    oldest_existing, latest_existing = _fetch_email_date_bounds(user_id)

    recent_days = max(1, settings.GMAIL_SMART_RECENT_DAYS)
    recent_lower_bound = max(
        requested_from or (requested_to - timedelta(days=recent_days - 1)),
        requested_to - timedelta(days=recent_days - 1),
    )
    backfill_lower_bound = requested_from or (requested_to - timedelta(days=max(1, settings.GMAIL_SYNC_MAX_LOOKBACK_DAYS)))

    sync_meta = _initial_meta(
        mode,
        requested_from=requested_from,
        requested_to=requested_to,
        backfill_complete=bool(existing_meta.get("backfill_complete", False)),
        oldest_synced_at=existing_meta.get("oldest_synced_at"),
        history_id=existing_history_id,
    )

    _set_sync_state(user_id, status="syncing", emails_total=0, emails_synced=0, history_id=existing_history_id, meta=sync_meta)

    try:
        access_token = await _refresh_access_token(decrypt_token(refresh_token_enc))
        async with httpx.AsyncClient(timeout=60, http2=True) as client:
            if mode == "incremental":
                incremental_start = requested_from
                if latest_existing:
                    overlap_days = max(0, settings.GMAIL_SYNC_OVERLAP_DAYS)
                    overlap_start = latest_existing - timedelta(days=overlap_days)
                    incremental_start = max(requested_from or overlap_start, overlap_start)
                elif incremental_start is None:
                    incremental_start = requested_to - timedelta(days=recent_days - 1)

                incremental_result = await _sync_range_windowed(
                    user_id,
                    client,
                    access_token,
                    start_date=incremental_start,
                    end_date=requested_to,
                    phase="incremental",
                    sync_meta={**sync_meta, "backfill_complete": bool(existing_meta.get("backfill_complete", False))},
                )
                sync_meta["history_id"] = incremental_result.get("history_id")
                sync_meta["oldest_synced_at"] = incremental_result.get("oldest_synced_at")
                sync_meta["backfill_complete"] = bool(existing_meta.get("backfill_complete", False))
            else:
                recent_result = await _sync_range_windowed(
                    user_id,
                    client,
                    access_token,
                    start_date=recent_lower_bound,
                    end_date=requested_to,
                    phase="recent",
                    sync_meta=sync_meta,
                )
                sync_meta["history_id"] = recent_result.get("history_id")
                sync_meta["oldest_synced_at"] = recent_result.get("oldest_synced_at")

                oldest_after_recent, _ = _fetch_email_date_bounds(user_id)
                existing_cursor_end = _parse_iso_date(existing_meta.get("backfill_cursor_end"))
                computed_backfill_end = oldest_after_recent - timedelta(days=1) if oldest_after_recent else None
                backfill_end = existing_cursor_end or computed_backfill_end
                backfill_complete = backfill_end is None or backfill_end < backfill_lower_bound

                if mode == "full":
                    backfill_complete = False if requested_from and requested_from < recent_lower_bound else backfill_complete

                if not backfill_complete:
                    if mode == "smart":
                        backfill_chunk_start = _window_start(backfill_end, backfill_lower_bound)
                        backfill_result = await _sync_window(
                            user_id,
                            client,
                            access_token,
                            window_start=backfill_chunk_start,
                            window_end=backfill_end,
                            phase="backfill",
                            sync_meta={**sync_meta, "backfill_complete": False},
                        )
                        sync_meta["history_id"] = backfill_result.get("history_id")
                        sync_meta["oldest_synced_at"] = backfill_result.get("oldest_synced_at")
                        remaining_cursor = backfill_chunk_start - timedelta(days=1)
                        sync_meta["backfill_complete"] = remaining_cursor < backfill_lower_bound
                        sync_meta["backfill_cursor_end"] = (
                            None if sync_meta["backfill_complete"] else _date_to_str(remaining_cursor)
                        )
                    else:
                        backfill_result = await _sync_range_windowed(
                            user_id,
                            client,
                            access_token,
                            start_date=backfill_lower_bound,
                            end_date=backfill_end,
                            phase="backfill",
                            sync_meta={**sync_meta, "backfill_complete": False},
                        )
                        sync_meta["history_id"] = backfill_result.get("history_id")
                        sync_meta["oldest_synced_at"] = backfill_result.get("oldest_synced_at")
                        sync_meta["backfill_complete"] = True
                        sync_meta["backfill_cursor_end"] = None
                else:
                    sync_meta["backfill_complete"] = True
                    sync_meta["backfill_cursor_end"] = None

        finished_at = _utc_now()
        indexed_total = _count_indexed_emails(user_id)
        done_detail = "Sync complete"
        if mode == "smart" and not bool(sync_meta.get("backfill_complete", True)):
            done_detail = "Recent sync complete. Run smart sync again to continue historical backfill."
        sync_meta.update({"phase": "complete", "detail": done_detail})
        _set_sync_state(
            user_id,
            status="done",
            emails_total=indexed_total,
            emails_synced=indexed_total,
            history_id=sync_meta.get("history_id"),
            last_synced_at=finished_at,
            meta=sync_meta,
        )
        return {
            "status": "done",
            "emails_total": indexed_total,
            "emails_synced": indexed_total,
            "last_synced_at": finished_at,
            "history_id": sync_meta.get("history_id"),
        }
    except Exception:
        sync_meta.update({"phase": "error", "detail": "Sync failed"})
        _set_sync_state(
            user_id,
            status="error",
            history_id=sync_meta.get("history_id"),
            meta=sync_meta,
        )
        raise
