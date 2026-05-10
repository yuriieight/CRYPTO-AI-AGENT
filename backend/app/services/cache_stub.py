"""Redis caching helper."""
import redis.asyncio as redis
import json
from app.core.config import settings

_redis: redis.Redis | None = None

async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def cache_get(key: str):
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None

async def cache_set(key: str, value, ttl: int = 60):
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value))
