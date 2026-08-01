import json

from app.agents.state import AgentState
from app.connectors.registry import get_connector
from app.execution.guardrails import enforce_table_allowlist


async def validate_query_node(state: AgentState) -> dict:
    query = state.get("generated_query")
    if not query:
        return {"error": "No query generated"}

    dialect = state["dialect"]
    connector = get_connector(dialect)
    validation = connector.validate_query(query)
    if not validation.valid:
        return {"error": validation.message}

    if state.get("query_language") == "sql":
        allowed_tables = state.get("allowed_tables")
        ok, msg = enforce_table_allowlist(query, allowed_tables)
        if not ok:
            return {"error": msg}

    if state.get("query_language") == "elasticsearch":
        allowed_indices = state.get("allowed_tables")
        if allowed_indices:
            try:
                index_name = json.loads(query).get("index", "")
            except json.JSONDecodeError:
                return {"error": "Invalid Elasticsearch query JSON"}
            if not any(idx in index_name or index_name in idx for idx in allowed_indices):
                return {"error": f"Query must target one of allowed indices: {allowed_indices}"}

    return {"error": None}
