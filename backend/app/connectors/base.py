from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ConnectionConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    schema_name: str | None = None
    ssl_mode: str | None = None
    auth_source: str | None = None


@dataclass
class ConnectionTestResult:
    success: bool
    message: str
    latency_ms: float | None = None


@dataclass
class ColumnInfo:
    name: str
    data_type: str
    nullable: bool = True
    is_pk: bool = False


@dataclass
class RelationshipInfo:
    column: str
    ref_table: str
    ref_column: str


@dataclass
class EntityInfo:
    name: str
    type: str  # table | collection
    columns: list[ColumnInfo] = field(default_factory=list)
    relationships: list[RelationshipInfo] = field(default_factory=list)
    sample_rows: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class SchemaSnapshot:
    entities: list[EntityInfo] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entities": [
                {
                    "name": e.name,
                    "type": e.type,
                    "columns": [
                        {
                            "name": c.name,
                            "data_type": c.data_type,
                            "nullable": c.nullable,
                            "is_pk": c.is_pk,
                        }
                        for c in e.columns
                    ],
                    "relationships": [
                        {"column": r.column, "ref_table": r.ref_table, "ref_column": r.ref_column}
                        for r in e.relationships
                    ],
                    "sample_rows": e.sample_rows,
                }
                for e in self.entities
            ]
        }


@dataclass
class QueryLimits:
    timeout_seconds: int = 30
    max_rows: int = 10000


@dataclass
class CompiledQuery:
    query: str
    language: str  # sql | mongodb | elasticsearch


@dataclass
class ResultColumn:
    name: str
    type: str


@dataclass
class QueryResult:
    columns: list[ResultColumn]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool = False
    duration_ms: int = 0


@dataclass
class ValidationResult:
    valid: bool
    message: str = ""


class DataSourceConnector(Protocol):
    dialect: str

    async def test_connection(self, config: ConnectionConfig) -> ConnectionTestResult: ...
    async def introspect_schema(self, config: ConnectionConfig) -> SchemaSnapshot: ...
    async def execute_read_query(
        self, config: ConnectionConfig, query: CompiledQuery, limits: QueryLimits
    ) -> QueryResult: ...
    def validate_query(self, query: str) -> ValidationResult: ...
