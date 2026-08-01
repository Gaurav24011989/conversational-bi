from uuid import UUID

from app.core.rbac import TenantContext


def schema_cache_key(org_id: UUID, project_id: UUID, datasource_id: UUID) -> str:
    return f"org:{org_id}:project:{project_id}:ds:{datasource_id}:schema"


def rate_limit_user_key(user_id: UUID) -> str:
    return f"ratelimit:user:{user_id}"


def rate_limit_org_key(org_id: UUID) -> str:
    return f"ratelimit:org:{org_id}"


def query_cache_key(org_id: UUID, datasource_id: UUID, query_hash: str) -> str:
    return f"org:{org_id}:ds:{datasource_id}:query:{query_hash}"
