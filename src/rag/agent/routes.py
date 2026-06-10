"""Small deterministic route helpers for the agent graph."""
from __future__ import annotations


def route_after_cache(max_rerank_score: float) -> str:
    return "agent_think" if max_rerank_score >= 1.0 else "rewrite_judge"


def route_after_rewrite(transformed_query: str) -> str:
    return "rewrite_exec" if transformed_query == "__REWRITE_NEEDED__" else "local_search"


def route_after_search(max_rerank_score: float, threshold: float) -> str:
    return "web_search_fallback" if max_rerank_score < threshold else "agent_think"


def route_after_agent(message) -> str:
    return "tools" if getattr(message, "tool_calls", None) else "finish"
