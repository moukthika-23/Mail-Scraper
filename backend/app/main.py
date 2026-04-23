from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, sync, search, analytics, analyse, queries
from app.services.sync_orchestrator import resume_auto_backfills_from_db

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Gmail Analysis Platform — REST API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
API_PREFIX = "/api/v1"
app.include_router(auth.router,      prefix=API_PREFIX + "/auth",      tags=["Auth"])
app.include_router(sync.router,      prefix=API_PREFIX + "/sync",      tags=["Sync"])
app.include_router(search.router,    prefix=API_PREFIX,                 tags=["Search"])
app.include_router(analytics.router, prefix=API_PREFIX + "/analytics",  tags=["Analytics"])
app.include_router(analyse.router,   prefix=API_PREFIX,                 tags=["Analyse"])
app.include_router(queries.router,   prefix=API_PREFIX + "/queries",    tags=["Queries"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.on_event("startup")
async def startup_events() -> None:
    # Reset stuck syncing states because the server restarted
    from app.core.db import supabase
    try:
        supabase.table("sync_state").update({"status": "idle"}).eq("status", "syncing").execute()
        print("[Gmail Sync] Reset any stuck 'syncing' states to 'idle'.")
    except Exception as e:
        print(f"[Gmail Sync] Failed to reset syncing states: {e}")

    # Preload the embedding model in a background thread so the first search doesn't timeout
    from app.services.search_service import get_embedding_model
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, get_embedding_model)
    print("[Search] Preloading embedding model...")

    resumed = await resume_auto_backfills_from_db()
    if resumed:
        print(f"[Gmail Sync] Resumed auto-backfill workers for {resumed} users")
