import json
from typing import Any, Optional
import redis.asyncio as redis
from app.core.config import settings

# Initialize Async Redis Client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def get_cache(key: str) -> Optional[Any]:
    """Retrieve JSON data from Redis cache."""
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"[Redis Get Error] {e}")
    return None

async def set_cache(key: str, value: Any, ttl: int = settings.CACHE_TTL_SECONDS) -> bool:
    """Store JSON data in Redis with an expiration (TTL)."""
    try:
        await redis_client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        print(f"[Redis Set Error] {e}")
        return False

async def cache_metadata_temporarily(user_id: str, metadata: list[dict]):
    """
    Optimization: Only metadata is stored temporarily during mass analysis.
    This prevents memory overload locally by keeping full body text out of RAM.
    """
    key = f"tmp_metadata:{user_id}"
    # Expire temporary metadata quickly (e.g., 5 minutes)
    await set_cache(key, metadata, ttl=300)
