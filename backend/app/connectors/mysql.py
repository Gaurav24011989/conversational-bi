import time

import aiomysql
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
from app.connectors.postgresql import BLOCKED_KEYWORDS


class MySQLConnector:
    dialect = "mysql"

    async def _connect(self, config: ConnectionConfig):
        return await aiomysql.connect(
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            db=config.database,
            connect_timeout=10,
        )

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult:
        start = time.monotonic()
        try:
            conn = await self._connect(config)
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
            conn.close()
            latency = (time.monotonic() - start) * 1000
            return ConnectionTestResult(success=True, message="Connection successful", latency_ms=latency)
        except Exception as e:
            return ConnectionTestResult(success=False, message=str(e))

    async def introspect_schema(self, config: ConnectionConfig) -> SchemaSnapshot:
        conn = await self._connect(config)
        schema = config.schema_name or config.database
        entities: list[EntityInfo] = []
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT TABLE_NAME FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                    """,
                    (schema,),
                )
                tables = await cur.fetchall()

                for table_row in tables:
                    table_name = table_row["TABLE_NAME"]
                    await cur.execute(
                        """
                        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY
                        FROM information_schema.COLUMNS
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                        ORDER BY ORDINAL_POSITION
                        """,
                        (schema, table_name),
                    )
                    columns_raw = await cur.fetchall()
                    columns = [
                        ColumnInfo(
                            name=c["COLUMN_NAME"],
                            data_type=c["DATA_TYPE"],
                            nullable=c["IS_NULLABLE"] == "YES",
                            is_pk=c["COLUMN_KEY"] == "PRI",
                        )
                        for c in columns_raw
                    ]

                    await cur.execute(
                        """
                        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                        FROM information_schema.KEY_COLUMN_USAGE
                        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                          AND REFERENCED_TABLE_NAME IS NOT NULL
                        """,
                        (schema, table_name),
                    )
                    fk_raw = await cur.fetchall()
                    relationships = [
                        RelationshipInfo(
                            column=r["COLUMN_NAME"],
                            ref_table=r["REFERENCED_TABLE_NAME"],
                            ref_column=r["REFERENCED_COLUMN_NAME"],
                        )
                        for r in fk_raw
                    ]

                    sample_rows: list[dict] = []
                    try:
                        await cur.execute(f"SELECT * FROM `{table_name}` LIMIT 3")
                        samples = await cur.fetchall()
                        for row in samples:
                            for k, v in row.items():
                                if hasattr(v, "isoformat"):
                                    row[k] = v.isoformat()
                                elif isinstance(v, bytes):
                                    row[k] = v.decode("utf-8", errors="replace")
                        sample_rows = samples
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
            conn.close()

    def validate_query(self, query: str) -> ValidationResult:
        stripped = query.strip().rstrip(";")
        if BLOCKED_KEYWORDS.search(stripped):
            return ValidationResult(valid=False, message="Query contains blocked keywords")
        parsed = sqlparse.parse(stripped)
        if len(parsed) != 1:
            return ValidationResult(valid=False, message="Only single statements allowed")
        upper = stripped.upper()
        if not (upper.startswith("SELECT") or upper.startswith("WITH")):
            return ValidationResult(valid=False, message="Query must start with SELECT or WITH")
        return ValidationResult(valid=True)

    async def execute_read_query(
        self, config: ConnectionConfig, query: CompiledQuery, limits: QueryLimits
    ) -> QueryResult:
        validation = self.validate_query(query.query)
        if not validation.valid:
            raise ValueError(validation.message)

        start = time.monotonic()
        conn = await self._connect(config)
        try:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(f"SET MAX_EXECUTION_TIME = {limits.timeout_seconds * 1000}")
                limited_query = query.query.strip().rstrip(";")
                if "LIMIT" not in limited_query.upper():
                    limited_query = f"{limited_query} LIMIT {limits.max_rows + 1}"
                await cur.execute(limited_query)
                rows_raw = await cur.fetchall()
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
                        elif isinstance(v, bytes):
                            row[k] = v.decode("utf-8", errors="replace")
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
            conn.close()
