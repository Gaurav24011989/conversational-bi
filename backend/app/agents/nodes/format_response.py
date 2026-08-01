from app.agents.state import AgentState
from app.i18n import t
from app.schemas import ChartType


ALLOWED_CHARTS = {c.value for c in ChartType}


def _validate_visualization(viz: dict, columns: list[str]) -> dict:
    chart_type = viz.get("chart_type", "table")
    if chart_type not in ALLOWED_CHARTS:
        chart_type = "table"

    x_field = viz.get("x_field")
    y_field = viz.get("y_field")

    if chart_type in ("pie", "donut") and (not x_field or not y_field):
        chart_type = "table"
    if chart_type in ("line", "area") and not x_field:
        chart_type = "table"
    if x_field and x_field not in columns:
        x_field = columns[0] if columns else None
    if y_field and y_field not in columns:
        y_field = columns[1] if len(columns) > 1 else None

    result = {
        "chart_type": chart_type,
        "title": viz.get("title"),
        "reasoning": viz.get("reasoning"),
        "series": [],
    }
    if x_field:
        result["x_axis"] = {"field": x_field, "label": x_field.replace("_", " ").title()}
    if y_field:
        result["y_axis"] = {"field": y_field, "label": y_field.replace("_", " ").title()}
        result["series"] = [{"field": y_field}]
    return result


async def format_response_node(state: AgentState) -> dict:
    error = state.get("error")
    viz_draft = state.get("visualization_draft") or {}
    query_result = state.get("query_result")
    locale = state.get("locale", "en")

    if error:
        response = {
            "type": "query_result",
            "locale": locale,
            "natural_language_query": state.get("natural_language_query", ""),
            "generated_query": state.get("generated_query"),
            "query_language": state.get("query_language"),
            "execution": {"status": "error", "row_count": None, "duration_ms": None, "truncated": False},
            "error": {"code": "QUERY_ERROR", "message": error},
            "follow_up_questions": state.get("follow_up_questions", []),
        }
        return {"response": response, "visualization": None}

    columns = [c["name"] for c in (query_result or {}).get("columns", [])]
    visualization = _validate_visualization(viz_draft, columns)

    response = {
        "type": "query_result",
        "locale": locale,
        "natural_language_query": state.get("natural_language_query", ""),
        "generated_query": state.get("generated_query"),
        "query_language": state.get("query_language"),
        "datasource": {
            "id": state["datasource_id"],
            "name": state.get("datasource_name", ""),
            "dialect": state["dialect"],
        },
        "execution": {
            "status": "success",
            "row_count": query_result.get("row_count") if query_result else 0,
            "duration_ms": query_result.get("duration_ms") if query_result else 0,
            "truncated": query_result.get("truncated", False) if query_result else False,
        },
        "data": query_result,
        "visualization": visualization,
        "follow_up_questions": state.get("follow_up_questions", []),
    }
    return {"response": response, "visualization": visualization}
