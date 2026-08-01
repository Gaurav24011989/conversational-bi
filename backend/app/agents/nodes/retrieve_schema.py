from pathlib import Path

from app.agents.state import AgentState


def _load_prompt_template() -> str:
    path = Path(__file__).parent.parent / "prompts" / "system_sql.md"
    return path.read_text()


def _select_relevant_entities(schema_context: dict, query: str, top_k: int = 10) -> dict:
    entities = schema_context.get("entities", [])
    if not entities:
        return schema_context

    query_lower = query.lower()
    scored = []
    for entity in entities:
        score = 0
        name = entity.get("name", "").lower()
        if name in query_lower:
            score += 10
        for col in entity.get("columns", []):
            col_name = col.get("name", "").lower()
            if col_name in query_lower:
                score += 3
        scored.append((score, entity))

    scored.sort(key=lambda x: x[0], reverse=True)
    relevant = [e for _, e in scored[:top_k] if _ > 0] or [e for _, e in scored[:top_k]]
    return {"entities": relevant}


async def retrieve_schema_node(state: AgentState) -> dict:
    schema = state.get("schema_context", {})
    nl_query = state.get("natural_language_query", "")
    relevant = _select_relevant_entities(schema, nl_query)
    return {"schema_context": relevant}
