from __future__ import annotations
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from collections import Counter, defaultdict

from app.core.db import supabase
from app.core.security import get_current_user_id

router = APIRouter()


class LabelFrequency(BaseModel):
    label: str
    count: int
    percentage: float


class VolumeDataPoint(BaseModel):
    date: str
    count: int


class SenderStat(BaseModel):
    sender_email: str
    sender_name: str
    domain: str
    count: int
    first_seen: str
    last_seen: str


class HeatmapCell(BaseModel):
    hour: int
    day: int
    count: int


class ThreadDepthBin(BaseModel):
    depth: str
    count: int


class AnalyticsSummary(BaseModel):
    total_emails: int
    total_senders: int
    total_labels: int
    total_threads: int
    avg_emails_per_day: float
    busiest_day: str
    busiest_hour: int
    top_label: str
    top_sender: str
    unread_count: int
    starred_count: int


def _get_emails(user_id: str):
    rows = []
    batch_size = 1000
    offset = 0
    while True:
        res = (
            supabase.table("emails")
            .select("id, date, is_read, is_starred, sender_email")
            .eq("user_id", user_id)
            .range(offset, offset + batch_size - 1)
            .execute()
        )
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
    return rows


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(user_id: str = Depends(get_current_user_id)):
    emails = _get_emails(user_id)
    senders_res = supabase.table("senders").select("id").eq("user_id", user_id).limit(10000).execute()
    labels_res = supabase.table("labels").select("id").eq("user_id", user_id).limit(1000).execute()
    threads_res = supabase.table("threads").select("id").eq("user_id", user_id).limit(10000).execute()

    total_emails = len(emails)
    total_senders = len(senders_res.data or [])
    total_labels = len(labels_res.data or [])
    total_threads = len(threads_res.data or [])

    unread_count = sum(1 for e in emails if e.get("is_read") is False)
    starred_count = sum(1 for e in emails if e.get("is_starred") is True)

    days = Counter()
    hours = Counter()
    dates = []

    for e in emails:
        d_str = e.get("date")
        if not d_str:
            continue
        try:
            dt = datetime.fromisoformat(d_str.replace("Z", "+00:00"))
            days[dt.strftime("%A")] += 1
            hours[dt.hour] += 1
            dates.append(dt)
        except ValueError:
            pass

    busiest_day = days.most_common(1)[0][0] if days else "N/A"
    busiest_hour = hours.most_common(1)[0][0] if hours else 0

    avg_emails = 0.0
    if dates:
        delta_days = max(1, (max(dates) - min(dates)).days)
        avg_emails = round(total_emails / delta_days, 1)

    top_sender = "N/A"
    top_sender_res = (
        supabase.table("senders")
        .select("name,domain")
        .eq("user_id", user_id)
        .order("total_count", desc=True)
        .limit(1)
        .execute()
    )
    if top_sender_res.data:
        row = top_sender_res.data[0]
        top_sender = row.get("name") or row.get("domain") or "N/A"

    top_label = "N/A"
    label_rows = (
        supabase.table("labels")
        .select("id,name")
        .eq("user_id", user_id)
        .limit(1000)
        .execute()
        .data
        or []
    )
    if label_rows:
        label_map = {row["id"]: row.get("name") or "N/A" for row in label_rows if row.get("id")}
        if label_map:
            label_usage = (
                supabase.table("email_labels")
                .select("label_id")
                .in_("label_id", list(label_map.keys()))
                .execute()
                .data
                or []
            )
            label_counts = Counter(row.get("label_id") for row in label_usage if row.get("label_id"))
            if label_counts:
                top_label = label_map[label_counts.most_common(1)[0][0]]

    return AnalyticsSummary(
        total_emails=total_emails,
        total_senders=total_senders,
        total_labels=total_labels,
        total_threads=total_threads,
        avg_emails_per_day=avg_emails,
        busiest_day=busiest_day,
        busiest_hour=busiest_hour,
        top_label=top_label,
        top_sender=top_sender,
        unread_count=unread_count,
        starred_count=starred_count,
    )


@router.get("/labels", response_model=list[LabelFrequency])
async def get_label_frequency(
    date_from: str = Query(default=""),
    date_to: str = Query(default=""),
    user_id: str = Depends(get_current_user_id),
):
    labels = supabase.table("labels").select("id, name").eq("user_id", user_id).execute().data or []
    if not labels:
        return []

    label_map = {l["id"]: l["name"] for l in labels}
    label_ids = list(label_map.keys())

    res = supabase.table("email_labels").select("label_id").in_("label_id", label_ids).execute().data or []
    counts = Counter(el.get("label_id") for el in res)

    total = sum(counts.values()) or 1
    freqs = []
    for lid, count in counts.most_common(10):
        freqs.append(LabelFrequency(
            label=label_map[lid],
            count=count,
            percentage=round((count / total) * 100, 1)
        ))
    return freqs


@router.get("/volume", response_model=list[VolumeDataPoint])
async def get_volume(
    date_from: str = Query(default=""),
    date_to: str = Query(default=""),
    granularity: str = Query(default="day"),
    user_id: str = Depends(get_current_user_id),
):
    emails = _get_emails(user_id)
    counts = Counter()
    for e in emails:
        d_str = e.get("date")
        if not d_str:
            continue
        try:
            dt = datetime.fromisoformat(d_str.replace("Z", "+00:00"))
            counts[dt.strftime("%Y-%m-%d")] += 1
        except Exception:
            pass

    start = datetime.strptime(date_from, "%Y-%m-%d") if date_from else datetime.now() - timedelta(days=30)
    end = datetime.strptime(date_to, "%Y-%m-%d") if date_to else datetime.now()
    delta = max(1, (end - start).days)

    res = []
    for i in range(delta + 1):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        res.append(VolumeDataPoint(date=d, count=counts.get(d, 0)))
    return res


@router.get("/senders", response_model=list[SenderStat])
async def get_top_senders(limit: int = Query(default=10), user_id: str = Depends(get_current_user_id)):
    senders = supabase.table("senders").select("email, name, domain, total_count, first_seen, last_seen").eq("user_id", user_id).order("total_count", desc=True).limit(limit).execute().data or []
    return [
        SenderStat(
            sender_email=s.get("email", ""),
            sender_name=s.get("name", ""),
            domain=s.get("domain", ""),
            count=s.get("total_count", 0),
            first_seen=s.get("first_seen") or "",
            last_seen=s.get("last_seen") or "",
        ) for s in senders
    ]


@router.get("/heatmap", response_model=list[HeatmapCell])
async def get_heatmap(
    date_from: str = Query(default=""),
    date_to: str = Query(default=""),
    user_id: str = Depends(get_current_user_id),
):
    emails = _get_emails(user_id)
    heatmap = defaultdict(int)
    for e in emails:
        d_str = e.get("date")
        if not d_str:
            continue
        try:
            dt = datetime.fromisoformat(d_str.replace("Z", "+00:00"))
            day = (dt.weekday() + 1) % 7
            heatmap[(day, dt.hour)] += 1
        except Exception:
            pass

    cells = []
    for day in range(7):
        for hour in range(24):
            cells.append(HeatmapCell(day=day, hour=hour, count=heatmap[(day, hour)]))
    return cells


@router.get("/threads", response_model=list[ThreadDepthBin])
async def get_threads(
    date_from: str = Query(default=""),
    date_to: str = Query(default=""),
    user_id: str = Depends(get_current_user_id),
):
    threads = supabase.table("threads").select("message_count").eq("user_id", user_id).execute().data or []
    bins = {"1": 0, "2–3": 0, "4–6": 0, "7–10": 0, "11+": 0}
    for t in threads:
        c = t.get("message_count", 1)
        if c == 1:
            bins["1"] += 1
        elif 2 <= c <= 3:
            bins["2–3"] += 1
        elif 4 <= c <= 6:
            bins["4–6"] += 1
        elif 7 <= c <= 10:
            bins["7–10"] += 1
        else:
            bins["11+"] += 1

    return [ThreadDepthBin(depth=k, count=v) for k, v in bins.items()]
