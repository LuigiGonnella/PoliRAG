from langchain_core.messages import AIMessage

from src.rag.agent.routes import (
    route_after_agent,
    route_after_cache,
    route_after_rewrite,
    route_after_search,
)
from src.rag.agent.tools import calculator


def test_route_after_cache():
    assert route_after_cache(1.0) == "agent_think"
    assert route_after_cache(0.99) == "rewrite_judge"


def test_route_after_rewrite():
    assert route_after_rewrite("__REWRITE_NEEDED__") == "rewrite_exec"
    assert route_after_rewrite("what is backpropagation") == "local_search"


def test_route_after_search():
    assert route_after_search(0.2, threshold=0.45) == "web_search_fallback"
    assert route_after_search(0.8, threshold=0.45) == "agent_think"


def test_route_after_agent_detects_tools():
    assert route_after_agent(AIMessage(content="done")) == "finish"
    message = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "calculator",
                "args": {"expression": "2 + 2"},
                "id": "call_1",
            }
        ],
    )
    assert route_after_agent(message) == "tools"


def test_calculator_tool_calling():
    assert calculator.invoke({"expression": "144 * 12"}) == "Calculation Result: 1728"
