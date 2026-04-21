import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import HTTPException
from groq import Groq

from app.core.cache import get_cache, set_cache
from app.core.config import settings
from app.core.db import supabase

groq_client = Groq(api_key=settings.GROQ_API_KEY)

SUPPORTED_ANALYSE_MODELS = (
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "groq/compound-mini",
)

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _compact_rows(rows: list[dict[str, Any]], key_name: str, max_rows: int = 12) -> list[dict[str, Any]]:
    compact = []
    for row in rows[:max_rows]:
        compact.append({key_name: row[key_name], "count": int(row["count"])})
    return compact


def _fetch_all_rows(
    table: str,
    select_cols: str,
    *,
    user_id: Optional[str] = None,
    in_filter: Optional[tuple[str, list[Any]]] = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    batch_size = 1000
    offset = 0
    while True:
        query = supabase.table(table).select(select_cols).range(offset, offset + batch_size - 1)
        if user_id is not None:
            query = query.eq("user_id", user_id)
        if in_filter is not None:
            field, values = in_filter
            query = query.in_(field, values)
        response = query.execute()
        batch = response.data or []
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
    return rows


def _sync_data_marker(user_id: str) -> str:
    row = (
        supabase.table("sync_state")
        .select("last_synced_at,emails_synced,history_id")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not row:
        return "no-sync"
    sync = row[0]
    return f"{sync.get('last_synced_at') or ''}:{sync.get('emails_synced') or 0}:{sync.get('history_id') or ''}"


def _build_context(user_id: str) -> dict[str, Any]:
    emails = _fetch_all_rows(
        "emails",
        "date, is_read, is_starred, sender_email, sender_name",
        user_id=user_id,
    )
    if not emails:
        raise HTTPException(
            status_code=409,
            detail="No synced inbox data is available yet. Run an inbox sync and try custom analysis again.",
        )

    senders = (
        supabase.table("senders")
        .select("email, name, domain, total_count, first_seen, last_seen")
        .eq("user_id", user_id)
        .order("total_count", desc=True)
        .limit(1000)
        .execute()
        .data
        or []
    )
    labels = (
        supabase.table("labels")
        .select("id, name")
        .eq("user_id", user_id)
        .limit(1000)
        .execute()
        .data
        or []
    )
    threads = (
        supabase.table("threads")
        .select("message_count")
        .eq("user_id", user_id)
        .limit(10000)
        .execute()
        .data
        or []
    )

    unread_count = sum(1 for email in emails if email.get("is_read") is False)
    starred_count = sum(1 for email in emails if email.get("is_starred") is True)

    date_counter: Counter[str] = Counter()
    weekday_counter: Counter[str] = Counter()
    hour_counter: Counter[str] = Counter()
    parsed_dates: list[datetime] = []

    for email in emails:
        dt = _parse_datetime(email.get("date"))
        if not dt:
            continue
        parsed_dates.append(dt)
        date_counter[dt.date().isoformat()] += 1
        weekday_counter[WEEKDAY_LABELS[dt.weekday()]] += 1
        hour_counter[f"{dt.hour:02d}:00"] += 1

    latest_date = max(parsed_dates, default=datetime.now(timezone.utc))
    start_date = latest_date.date() - timedelta(days=29)
    recent_volume: list[dict[str, Any]] = []
    for offset in range(30):
        current_day = start_date + timedelta(days=offset)
        current_key = current_day.isoformat()
        recent_volume.append({"date": current_key, "count": date_counter.get(current_key, 0)})

    top_senders: list[dict[str, Any]] = []
    domain_counter: Counter[str] = Counter()
    for sender in senders:
        count = int(sender.get("total_count") or 0)
        sender_name = sender.get("name") or sender.get("email") or sender.get("domain") or "Unknown sender"
        top_senders.append({"sender": sender_name, "count": count})
        domain = sender.get("domain") or ""
        if not domain and sender.get("email") and "@" in sender["email"]:
            domain = sender["email"].split("@", 1)[1].lower()
        if domain:
            domain_counter[domain] += count

    top_domains = [{"domain": domain, "count": count} for domain, count in domain_counter.most_common(12)]

    label_distribution: list[dict[str, Any]] = []
    label_ids = [label["id"] for label in labels if label.get("id")]
    if label_ids:
        label_map = {label["id"]: label.get("name") or "Unknown" for label in labels if label.get("id")}
        label_usage = _fetch_all_rows("email_labels", "label_id", in_filter=("label_id", label_ids))
        label_counts = Counter(row.get("label_id") for row in label_usage if row.get("label_id"))
        label_distribution = [
            {"label": label_map[label_id], "count": count}
            for label_id, count in label_counts.most_common(12)
            if label_id in label_map
        ]

    thread_bins = {"1": 0, "2-3": 0, "4-6": 0, "7-10": 0, "11+": 0}
    for thread in threads:
        depth = int(thread.get("message_count") or 1)
        if depth <= 1:
            thread_bins["1"] += 1
        elif depth <= 3:
            thread_bins["2-3"] += 1
        elif depth <= 6:
            thread_bins["4-6"] += 1
        elif depth <= 10:
            thread_bins["7-10"] += 1
        else:
            thread_bins["11+"] += 1

    if parsed_dates:
        span_days = max(1, (max(parsed_dates) - min(parsed_dates)).days)
        avg_per_day = round(len(emails) / span_days, 1)
    else:
        avg_per_day = 0.0

    return {
        "summary": {
            "total_emails": len(emails),
            "total_senders": len(senders),
            "total_labels": len(labels),
            "total_threads": len(threads),
            "unread_count": unread_count,
            "starred_count": starred_count,
            "avg_emails_per_day": avg_per_day,
        },
        "available_dimensions": [
            "date",
            "hour of day",
            "weekday",
            "sender",
            "sender domain",
            "label",
            "thread depth",
            "read status",
            "starred status",
        ],
        "datasets": {
            "daily_volume_last_30_days": recent_volume,
            "top_sender_domains": _compact_rows(top_domains, "domain"),
            "top_senders": _compact_rows(top_senders, "sender"),
            "label_distribution": _compact_rows(label_distribution, "label"),
            "hourly_activity": [
                {"hour": f"{hour:02d}:00", "count": hour_counter.get(f"{hour:02d}:00", 0)}
                for hour in range(24)
            ],
            "weekday_activity": [{"day": day, "count": weekday_counter.get(day, 0)} for day in WEEKDAY_LABELS],
            "thread_depth_distribution": [{"depth": depth, "count": count} for depth, count in thread_bins.items()],
            "read_status": [
                {"status": "Unread", "count": unread_count},
                {"status": "Read", "count": len(emails) - unread_count},
            ],
            "starred_status": [
                {"status": "Starred", "count": starred_count},
                {"status": "Not Starred", "count": len(emails) - starred_count},
            ],
        },
    }


def _candidate_models() -> list[str]:
    ordered_models = [settings.GROQ_ANALYSE_MODEL, *SUPPORTED_ANALYSE_MODELS]
    seen: set[str] = set()
    models: list[str] = []
    for model in ordered_models:
        if model and model not in seen:
            seen.add(model)
            models.append(model)
    return models


def _parse_chart_spec(raw_text: str) -> dict[str, Any]:
    json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    payload = json_match.group(0) if json_match else raw_text
    parsed = json.loads(payload)
    if not isinstance(parsed.get("data"), list):
        raise ValueError("Chart spec must contain a list in the `data` field.")
    if parsed.get("type") not in {"bar", "line", "pie", "scatter", "heatmap", "table"}:
        parsed["type"] = "bar"
    return parsed


async def generate_dynamic_analysis(user_id: str, query: str, preferred_chart_type: Optional[str] = None) -> dict[str, Any]:
    """
    Generate a chart specification from real inbox aggregates.
    Cached per user/query to avoid unnecessary LLM calls.
    """
    cache_key_raw = f"analysis:{user_id}:{query}:{preferred_chart_type or 'auto'}:{_sync_data_marker(user_id)}"
    cache_key = hashlib.md5(cache_key_raw.encode()).hexdigest()

    cached_spec = await get_cache(cache_key)
    if cached_spec:
        print("[Redis] Cache HIT. Returning grounded analysis spec.")
        return cached_spec

    context = _build_context(user_id)
    context_json = json.dumps(context, separators=(",", ":"), ensure_ascii=True)
    chart_constraint = (
        f"Use preferred chart type `{preferred_chart_type}` if it fits the request."
        if preferred_chart_type
        else "Select the most appropriate chart type from bar, line, pie, scatter, heatmap, or table."
    )

    system_prompt = f"""You are MailLens Advanced Analytics Engine.
You are given real inbox analytics aggregates for one authenticated user.
Answer ONLY with numbers and categories that can be derived from the provided datasets.
Never invent senders, labels, domains, dates, or counts.

Return a strictly valid JSON object with this exact structure:
{{
  "type": "bar" | "line" | "pie" | "scatter" | "heatmap" | "table",
  "title": "<String>",
  "x_label": "<Key present in every data row>",
  "y_label": "<Key present in every data row>",
  "data": [{{}}],
  "explanation": "<Short explanation grounded in the provided data>"
}}

Rules:
- Output JSON only. No markdown.
- Keep `data` to at most 12 rows unless the query clearly asks for a time series.
- If the query asks for unsupported metrics like attachments, body semantics, or reply latency, choose the closest available real dataset and explain the limitation.
- `x_label` and `y_label` must exactly match keys present in every data row.
- Prefer the most relevant dataset from the provided inbox context.
- {chart_constraint}

Inbox context JSON:
{context_json}
"""

    errors: list[str] = []
    for model in _candidate_models():
        try:
            completion = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.2,
                max_tokens=900,
            )
            raw_text = completion.choices[0].message.content or ""
            spec_json = _parse_chart_spec(raw_text)
            await set_cache(cache_key, spec_json, ttl=3600)
            return spec_json
        except Exception as exc:
            errors.append(f"{model}: {exc}")

    print("[Analyse Error] " + " | ".join(errors))
    raise HTTPException(
        status_code=502,
        detail="Live analysis is unavailable. Check the Groq API key and inbox backend configuration.",
    )
