import re

import sqlparse

BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|"
    r"MERGE|CALL|COPY|LOAD|INTO|SET)\b",
    re.IGNORECASE,
)


def validate_sql_query(query: str) -> tuple[bool, str]:
    stripped = query.strip().rstrip(";")
    if BLOCKED_KEYWORDS.search(stripped):
        return False, "Query contains blocked keywords"
    parsed = sqlparse.parse(stripped)
    if len(parsed) != 1:
        return False, "Only single statements allowed"
    upper = stripped.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "Query must start with SELECT or WITH"
    return True, ""


def enforce_table_allowlist(query: str, allowed_tables: list[str] | None) -> tuple[bool, str]:
    if not allowed_tables:
        return True, ""
    upper = query.upper()
    for table in allowed_tables:
        if table.upper() in upper:
            return True, ""
    return False, f"Query must reference one of allowed tables: {allowed_tables}"
