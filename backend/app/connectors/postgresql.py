import re
import time

import asyncpg
import sqlparse

from app.connectors.base import (
    ColumnInfo,
    CompiledQuery,
    ConnectionConfig,
    ConnectionTestResult,
    EntityInfo,
    QueryLimits,
    QueryResult,
    RelationshipInfo,
    ResultColumn,
    SchemaSnapshot,
    ValidationResult,
)

BLOCKED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE|"
    r"MERGE|CALL|COPY|LOAD|INTO|SET)\b",
    re.IGNORECASE,
)


class PostgreSQLConnector:
    dialect = "postgresql"

    def _dsn(self, config: ConnectionConfig) -> str:
        return (
            f"postgresql://{config.username}:{config.password}"
            f"@{config.host}:{config.port}/{config.database}"
        )

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        start = time.monotonic()
        try:
            conn = await asyncpg.connect(self._dsn(config), timeout=10)
            await conn.fetchval("SELECT 1")
            await conn.close()
            latency = (time.monotonic() - start) * 1000
            return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)
        except Exception as e:
            return ConnectionTestResult(success=False, message=str(e))

    async def introspect_schema(self, config: ConnectionConfig) -> SchemaSnapshot:
        schema = config.schema_name or "public"
        conn = await asyncpg.connect(self._dsn(config), timeout=30)
        try:
            tables = await conn.fetch(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = $1 AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """,
                schema,
            )

            entities: list[EntityInfo] = []
            for table_row in tables:
                table_name = table_row["table_name"]
                columns_raw = await conn.fetch(
                    """
                    SELECT column_name, data_type, is_nullable,
                           (SELECT COUNT(*) > 0 FROM information_schema.table_constraints tc
                            JOIN information_schema.key_column_usage kcu
                              ON tc.constraint_name = kcu.constraint_name
                            WHERE tc.table_schema = $1 AND tc.table_name = $2
                              AND kcu.column_name = c.column_name
                              AND tc.constraint_type = 'PRIMARY KEY') AS is_pk
                    FROM information_schema.columns c
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """,
                    schema,
                    table_name,
                )
                columns = [
                    ColumnInfo(
                        name=c["column_name"],
                        data_type=c["data_type"],
                        nullable=c["is_nullable"] == "YES",
                        is_pk=c["is_pk"],
                    )
                    for c in columns_raw
                ]

                fk_raw = await conn.fetch(
                    """
                    SELECT kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_column
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage ccu
                      ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                      AND tc.table_schema = $1 AND tc.table_name = $2
                    """,
                    schema,
                    table_name,
                )
                relationships = [
                    RelationshipInfo(
                        column=r["column_name"],
                        ref_table=r["ref_table"],
                        ref_column=r["ref_column"],
                    )
                    for r in fk_raw
                ]

                sample_rows: list[dict] = []
                try:
                    samples = await conn.fetch(
                        f'SELECT * FROM "{schema}"."{table_name}" LIMIT 3'
                    )
                    sample_rows = [dict(r) for r in samples]
                    for row in sample_rows:
                        for k, v in row.items():
                            if hasattr(v, "isoformat"):
                                row[k] = v.isoformat()
                            elif not isinstance(v, (str, int, float, bool, type(None))):
                                row[k] = str(v)
                except Exception:
                    pass

                entities.append(
                    EntityInfo(
                        name=table_name,
                        type="table",
                        columns=columns,
                        relationships=relationships,
                        sample_rows=sample_rows,
                    )
                )
            return SchemaSnapshot(entities=entities)
        finally:
            await conn.close()

    def validate_query(self, query: str) -> ValidationResult:
        stripped = query.strip().rstrip(";")
        if BLOCKED_KEYWORDS.search(stripped):
            return ValidationResult(valid=False, message="Query contains blocked keywords")
        parsed = sqlparse.parse(stripped)
        if len(parsed) != 1:
            return ValidationResult(valid=False, message="Only single statements allowed")
        stmt = parsed[0]
        stmt_type = stmt.get_type()
        if stmt_type not in ("SELECT", "UNKNOWN"):
            return ValidationResult(valid=False, message=f"Only SELECT allowed, got {stmt_type}")
        upper = stripped.upper()
        if not (upper.startswith(("SELECT", "WITH"))):
            return ValidationResult(valid=False, message="Query must start with SELECT or WITH")
        return ValidationResult(valid=True)

    async def execute_read_query(
        self, config: ConnectionConfig, query: CompiledQuery, limits: QueryLimits
    ) -> QueryResult:
        validation = self.validate_query(query.query)
        if not validation.valid:
            raise ValueError(validation.message)

        start = time.monotonic()
        conn = await asyncpg.connect(self._dsn(config), timeout=limits.timeout_seconds)
        try:
            await conn.execute(f"SET statement_timeout = '{limits.timeout_seconds * 1000}'")
            limited_query = query.query.strip().rstrip(";")
            if "LIMIT" not in limited_query.upper():
                limited_query = f"{limited_query} LIMIT {limits.max_rows + 1}"

            rows_raw = await conn.fetch(limited_query)
            truncated = len(rows_raw) > limits.max_rows
            rows_raw = rows_raw[: limits.max_rows]

            columns: list[ResultColumn] = []
            if rows_raw:
                for key in rows_raw[0]:
                    columns.append(ResultColumn(name=key, type="unknown"))

            rows: list[dict] = []
            for r in rows_raw:
                row = dict(r)
                for k, v in row.items():
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif not isinstance(v, (str, int, float, bool, type(None))):
                        row[k] = str(v)
                rows.append(row)

            duration = int((time.monotonic() - start) * 1000)
            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                duration_ms=duration,
            )
        finally:
            await conn.close()
