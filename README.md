# MailLens 🔍

**AI-Powered Gmail Analysis Platform**

A self-hosted, zero-cost web app that connects to your Gmail account and surfaces hidden inbox intelligence through LLM-powered search, interactive charts, and a free-form custom query engine.

---

## ✨ Features

| Feature | Status |
|---|---|
| **Smart Search** — Semantic + keyword hybrid search with Groq LLM synthesis | ✅ Frontend complete |
| **Analytics Dashboard** — Volume, labels, senders, heatmap, thread depth | ✅ Frontend complete |
| **AI Analysis Studio** — Natural language → interactive chart via Groq LLM | ✅ Frontend complete |
| **Gmail OAuth Sync** — Read-only Gmail ingestion via Gmail API | 🔧 Backend scaffold |
| **pgvector Embeddings** — Sentence-transformer semantic search over email bodies | 🔧 Backend scaffold |
| **Custom Query Engine** — LLM translates queries to SQL-like analysis specs | ✅ Frontend + 🔧 Backend |

---

## 🏗 Architecture

```
frontend/  — React 18 + Vite + TypeScript + Recharts + TanStack Query
backend/   — Python 3.11 + FastAPI + Celery + Supabase + Groq API
```

## 🚀 Quick Start (Real Data Mode)

```bash
cd frontend
npm install
npm run dev        # → http://localhost:5173
```

The frontend is wired for real data by default. Point `VITE_API_URL` at your backend and keep `VITE_MOCK_MODE=false` for normal use.

If you want a local demo without live services, set `VITE_MOCK_MODE=true` in `frontend/.env` to opt into the mock fixtures.

## 🔧 Backend Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
uvicorn app.main:app --reload
```

The backend requires real Supabase, Google OAuth, and Groq credentials. It no longer silently swaps in a dummy database client when those values are missing.

### Gmail sync behavior

- `smart` sync indexes recent mail first (`GMAIL_SMART_RECENT_DAYS`) so the app is usable quickly.
- Historical mail is backfilled in resumable windows (`GMAIL_BACKFILL_WINDOW_DAYS`) and advances one window per smart-sync run.
- `incremental` sync focuses on newest mail with a small overlap (`GMAIL_SYNC_OVERLAP_DAYS`) to avoid misses.
- Per-request Gmail paging is controlled by `GMAIL_PAGE_SIZE` and detail fetch concurrency by `GMAIL_CONCURRENCY`.
- Auto-continue backfill is enabled by default and can be tuned with `GMAIL_AUTO_BACKFILL_*` settings.

## 📦 Tech Stack (100% Free Tier)

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite + Recharts + TanStack Query + Zustand |
| Backend | FastAPI + Celery + APScheduler |
| Database | Supabase PostgreSQL + pgvector |
| LLM | Groq API — llama-3.1-8b-instant / llama-3.3-70b-versatile |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Cache | Upstash Redis |
| Hosting | Vercel (frontend) + Hugging Face Spaces (backend) |

## 🔑 Environment Variables

Copy `frontend/.env` and `backend/.env.example` and fill in:

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — [Google Cloud Console](https://console.cloud.google.com)
- `GROQ_API_KEY` — [console.groq.com](https://console.groq.com)
- `SUPABASE_URL` / keys — [supabase.com](https://supabase.com)
