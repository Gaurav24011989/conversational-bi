from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ORG_ADMIN = "org_admin"
    PROJECT_ADMIN = "project_admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class DataSourceType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MONGODB = "mongodb"
    ELASTICSEARCH = "elasticsearch"


class ChartType(str, Enum):
    TABLE = "table"
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    METRIC = "metric"
    HEATMAP = "heatmap"


# Auth schemas
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    org_name: str
    org_slug: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    org_id: UUID
    is_active: bool
    preferred_locale: str | None = None

    model_config = {"from_attributes": True}


class UserLocaleUpdate(BaseModel):
    preferred_locale: str = Field(..., min_length=2, max_length=10)


class LocaleInfo(BaseModel):
    code: str
    name: str
    native_name: str


class LocalesResponse(BaseModel):
    default_locale: str
    supported_locales: list[LocaleInfo]


# Organization & Project
class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    name: str
    description: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    org_id: UUID
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectMembershipCreate(BaseModel):
    user_id: UUID
    role: UserRole = UserRole.ANALYST
    datasource_id: UUID | None = None


# Data source schemas
class DataSourceConfig(BaseModel):
    host: str
    port: int
    database: str  # DB name, MongoDB database, or Elasticsearch default index pattern
    username: str = ""
    password: str = ""
    schema_name: str | None = None
    ssl_mode: str | None = None  # set to "require" for Elasticsearch HTTPS
    auth_source: str | None = None  # MongoDB auth source


class DataSourceCreate(BaseModel):
    name: str
    type: DataSourceType
    config: DataSourceConfig
    allowed_tables: list[str] | None = None


class DataSourceResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    type: DataSourceType
    is_active: bool
    allowed_tables: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: float | None = None


class SchemaSnapshotResponse(BaseModel):
    id: UUID
    datasource_id: UUID
    version: int
    schema_data: dict[str, Any]
    captured_at: datetime

    model_config = {"from_attributes": True}


# Conversation schemas
class ConversationCreate(BaseModel):
    datasource_id: UUID
    title: str | None = None


class ConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    datasource_id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    locale: str | None = Field(
        default=None,
        min_length=2,
        max_length=10,
        description="BCP-47 locale code (e.g. en, fr, de, es, hi, zh)",
    )


class AxisConfig(BaseModel):
    field: str
    label: str | None = None


class SeriesConfig(BaseModel):
    field: str
    label: str | None = None


class VisualizationConfig(BaseModel):
    chart_type: ChartType
    title: str | None = None
    x_axis: AxisConfig | None = None
    y_axis: AxisConfig | None = None
    series: list[SeriesConfig] = []
    reasoning: str | None = None


class ColumnInfo(BaseModel):
    name: str
    type: str


class DataPayload(BaseModel):
    columns: list[ColumnInfo]
    rows: list[dict[str, Any]]


class ExecutionInfo(BaseModel):
    status: str
    row_count: int | None = None
    duration_ms: int | None = None
    truncated: bool = False


class ErrorInfo(BaseModel):
    code: str
    message: str


class DataSourceInfo(BaseModel):
    id: UUID
    name: str
    dialect: str


class QueryResponse(BaseModel):
    message_id: UUID
    conversation_id: UUID
    role: str = "assistant"
    type: str = "query_result"
    locale: str | None = None
    natural_language_query: str
    generated_query: str | None = None
    query_language: str | None = None
    datasource: DataSourceInfo | None = None
    execution: ExecutionInfo
    data: DataPayload | None = None
    visualization: VisualizationConfig | None = None
    follow_up_questions: list[str] = []
    trace_id: str | None = None
    error: ErrorInfo | None = None


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    response_data: QueryResponse | dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClarificationResponse(BaseModel):
    message_id: UUID
    conversation_id: UUID
    role: str = "assistant"
    type: str = "clarification"
    questions: list[str]
    trace_id: str | None = None
