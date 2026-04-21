from supabase import Client, create_client

from app.core.config import settings


def _build_supabase_client() -> Client:
    """Create the real Supabase client or fail fast if credentials are missing."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY are required for real inbox data. "
            "Fill backend/.env instead of relying on the old dummy client."
        )

    try:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    except Exception as exc:
        raise RuntimeError(f"Supabase client initialization failed: {exc}") from exc


supabase: Client = _build_supabase_client()
