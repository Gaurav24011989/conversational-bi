from uuid import UUID

from app.agents.state import AgentState
from app.connectors.base import ConnectionConfig
from app.execution.executor import executor


async def execute_query_node(state: AgentState) -> dict:
    try:
        config_dict = state["connection_config"]
        config = ConnectionConfig(**config_dict)
        result = await executor.execute(
            dialect=state["dialect"],
            config=config,
            query=state["generated_query"],
            query_language=state.get("query_language", "sql"),
            datasource_id=UUID(state["datasource_id"]),
            allowed_tables=state.get("allowed_tables"),
        )
        return {
            "query_result": {
                "columns": [{"name": c.name, "type": c.type} for c in result.columns],
                "rows": result.rows,
                "row_count": result.row_count,
                "truncated": result.truncated,
                "duration_ms": result.duration_ms,
            },
            "error": None,
        }
    except Exception as e:
        return {"error": str(e), "query_result": None}
