from langgraph.graph import END, StateGraph

from app.agents.nodes.execute_query import execute_query_node
from app.agents.nodes.format_response import format_response_node
from app.agents.nodes.generate_query import generate_query_node
from app.agents.nodes.retrieve_schema import retrieve_schema_node
from app.agents.nodes.validate_query import validate_query_node
from app.agents.state import AgentState


def should_execute(state: AgentState) -> str:
    if state.get("error"):
        return "format"
    if state.get("generated_query"):
        return "validate"
    return "format"


def after_validate(state: AgentState) -> str:
    if state.get("error"):
        return "format"
    return "execute"


def build_query_agent():
    graph = StateGraph(AgentState)

    graph.add_node("retrieve_schema", retrieve_schema_node)
    graph.add_node("generate_query", generate_query_node)
    graph.add_node("validate_query", validate_query_node)
    graph.add_node("execute_query", execute_query_node)
    graph.add_node("format_response", format_response_node)

    graph.set_entry_point("retrieve_schema")
    graph.add_edge("retrieve_schema", "generate_query")
    graph.add_conditional_edges(
        "generate_query", should_execute, {"validate": "validate_query", "format": "format_response"}
    )
    graph.add_conditional_edges(
        "validate_query", after_validate, {"execute": "execute_query", "format": "format_response"}
    )
    graph.add_edge("execute_query", "format_response")
    graph.add_edge("format_response", END)

    return graph.compile()


query_agent = build_query_agent()
