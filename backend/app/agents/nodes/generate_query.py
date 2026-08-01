import json
from pathlib import Path

from langchain_core.messages import SystemMessage

from app.agents.state import AgentState, GeneratedQueryOutput
from app.llm.factory import get_chat_model


_PROMPT_FILES = {
    "postgresql": "system_sql.md",
    "mysql": "system_sql.md",
    "mongodb": "system_sql.md",
    "elasticsearch": "system_elasticsearch.md",
}


def _load_prompt(dialect: str, schema_json: str) -> str:
    filename = _PROMPT_FILES.get(dialect, "system_sql.md")
    path = Path(__file__).parent.parent / "prompts" / filename
    template = path.read_text()
    return template.format(dialect=dialect, schema_json=schema_json)


async def generate_query_node(state: AgentState) -> dict:
    try:
        llm = get_chat_model()
        structured_llm = llm.with_structured_output(GeneratedQueryOutput)

        schema_json = json.dumps(state.get("schema_context", {}), indent=2, default=str)
        system_prompt = _load_prompt(state["dialect"], schema_json)

        messages = [
            SystemMessage(content=system_prompt),
            *state.get("messages", []),
        ]

        result: GeneratedQueryOutput = await structured_llm.ainvoke(messages)

        return {
            "generated_query": result.query,
            "query_language": result.query_language,
            "explanation": result.explanation,
            "visualization_draft": result.visualization.model_dump(),
            "follow_up_questions": result.follow_up_questions,
            "error": None,
        }
    except Exception as e:
        return {
            "error": f"Failed to generate query: {e}",
            "generated_query": None,
        }
