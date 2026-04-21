from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ENV_FILE = str(Path(__file__).resolve().parents[2] / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_ENV_FILE, extra="ignore")

    # App
    APP_NAME: str = "MailLens API"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    DATABASE_URL: str = ""  # postgres+asyncpg://...

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/callback"

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_SEARCH_MODEL: str = "llama-3.1-8b-instant"
    GROQ_ANALYSE_MODEL: str = "llama-3.3-70b-versatile"

    # Redis (Upstash)
    REDIS_URL: str = "redis://localhost:6379"

    # Sync
    GMAIL_MAX_RESULTS: int = 500
    GMAIL_PAGE_SIZE: int = 100
    GMAIL_CONCURRENCY: int = 20
    GMAIL_SYNC_FULL_BODY: bool = False
    GMAIL_SMART_RECENT_DAYS: int = 30
    GMAIL_BACKFILL_WINDOW_DAYS: int = 30
    GMAIL_SYNC_OVERLAP_DAYS: int = 2
    GMAIL_SYNC_MAX_LOOKBACK_DAYS: int = 3650
    GMAIL_AUTO_BACKFILL_ENABLED: bool = True
    GMAIL_AUTO_BACKFILL_INITIAL_DELAY_SECONDS: int = 15
    GMAIL_AUTO_BACKFILL_INTERVAL_SECONDS: int = 30
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    SEARCH_TOP_K: int = 20
    CACHE_TTL_SECONDS: int = 3600

    # CORS
    FRONTEND_URL: str = "http://localhost:5173"


settings = Settings()
