from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class VisualizationDraft(BaseModel):
    chart_type: str = "table"
    title: str | None = None
    x_field: str | None = None
    y_field: str | None = None
    group_by: str | None = None
    reasoning: str | None = None


class GeneratedQueryOutput(BaseModel):
    query: str
    query_language: Literal["sql", "mongodb"]
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = ""
    visualization: VisualizationDraft = Field(default_factory=VisualizationDraft)
    follow_up_questions: list[str] = Field(default_factory=list)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    org_id: str
    project_id: str
    datasource_id: str
    datasource_name: str
    dialect: str
    connection_config: dict[str, Any]
    allowed_tables: list[str] | None
    schema_context: dict[str, Any]
    natural_language_query: str
    generated_query: str | None
    query_language: str | None
    explanation: str | None
    visualization_draft: dict[str, Any] | None
    follow_up_questions: list[str]
    query_result: dict[str, Any] | None
    visualization: dict[str, Any] | None
    response: dict[str, Any] | None
    error: str | None
    trace_id: str | None
