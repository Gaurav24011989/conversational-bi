import json
from typing import Any
from uuid import UUID

import redis.asyncio as aioredis

from app.config import settings
from app.core.tenancy import query_cache_key, rate_limit_org_key, rate_limit_user_key, schema_cache_key

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


class CacheService:
    SCHEMA_TTL = 3600  # 1 hour
    QUERY_TTL = 300  # 5 minutes

    async def get_schema(self, org_id: UUID, project_id: UUID, datasource_id: UUID) -> dict | None:
        redis = await get_redis()
        key = schema_cache_key(org_id, project_id, datasource_id)
        data = await redis.get(key)
        return json.loads(data) if data else None

    async def set_schema(
        self, org_id: UUID, project_id: UUID, datasource_id: UUID, schema: dict[str, Any]
    ) -> None:
        redis = await get_redis()
        key = schema_cache_key(org_id, project_id, datasource_id)
        await redis.setex(key, self.SCHEMA_TTL, json.dumps(schema, default=str))

    async def invalidate_schema(self, org_id: UUID, project_id: UUID, datasource_id: UUID) -> None:
        redis = await get_redis()
        key = schema_cache_key(org_id, project_id, datasource_id)
        await redis.delete(key)

    async def get_query_cache(
        self, org_id: UUID, datasource_id: UUID, query_hash: str
    ) -> dict | None:
        redis = await get_redis()
        key = query_cache_key(org_id, datasource_id, query_hash)
        data = await redis.get(key)
        return json.loads(data) if data else None

    async def set_query_cache(
        self, org_id: UUID, datasource_id: UUID, query_hash: str, result: dict[str, Any]
    ) -> None:
        redis = await get_redis()
        key = query_cache_key(org_id, datasource_id, query_hash)
        await redis.setex(key, self.QUERY_TTL, json.dumps(result, default=str))


cache_service = CacheService()


class RateLimiter:
    WINDOW_SECONDS = 60

    async def check_rate_limit(self, user_id: UUID, org_id: UUID) -> tuple[bool, str]:
        redis = await get_redis()
        user_key = rate_limit_user_key(user_id)
        org_key = rate_limit_org_key(org_id)

        pipe = redis.pipeline()
        pipe.incr(user_key)
        pipe.expire(user_key, self.WINDOW_SECONDS)
        pipe.incr(org_key)
        pipe.expire(org_key, self.WINDOW_SECONDS)
        results = await pipe.execute()

        user_count = results[0]
        org_count = results[2]

        if user_count > settings.rate_limit_per_user:
            return False, "User rate limit exceeded"
        if org_count > settings.rate_limit_per_org:
            return False, "Organization rate limit exceeded"
        return True, ""


rate_limiter = RateLimiter()
