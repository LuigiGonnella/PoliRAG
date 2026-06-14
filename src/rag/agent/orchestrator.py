"""LangGraph orchestration for the PoliRAG agent."""
from __future__ import annotations

import logging
from typing import Annotated, List, TypedDict

from langchain_core.messages import HumanMessage, RemoveMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from qdrant_client import QdrantClient

from src.rag.agent.llm_config import LLMConfig
from src.rag.agent.routes import (
    route_after_agent,
    route_after_cache,
    route_after_rewrite,
    route_after_search,
)
from src.rag.agent.tools import calculator, external_web_search, run_python
from src.rag.query_transform.query_rewriter import QueryRewriter
from src.rag.reranking.reranker_pipeline import RerankerPipeline
from src.rag.retrieval.retrieval_pipeline import RetrievalPipeline

try:
    from google import genai
    from google.genai import types
except Exception:  # pragma: no cover - optional dependency path
    genai = None
    types = None


logger = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    transformed_query: str
    course_filter: str
    degree_filter: str
    year_filter: str
    retrieved_context: str
    context_cache: List[dict]
    ltm_summary: str
    max_rerank_score: float
    citations: List[dict]


class PolyRAGAgent:
    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        hf_token: str | None,
        llm_config,
        *,
        hf_embedding_model: str = "BAAI/bge-small-en-v1.5",
        fastembed_cache_dir: str | None = None,
        llm_request_timeout_seconds: int = 60,
        web_search_timeout_seconds: int = 12,
        enable_web_fallback: bool = True,
        enable_python_tool: bool = False,
        retrieval_top_k: int = 25,
        rerank_top_l: int = 5,
        fallback_threshold: float = 0.45,
    ):
        self.hf_token = hf_token
        self.llm_config = LLMConfig.coerce(llm_config)
        api_key = self.llm_config.require_api_key()
        self.enable_web_fallback = enable_web_fallback
        self.retrieval_top_k = retrieval_top_k
        self.rerank_top_l = rerank_top_l
        self.fallback_threshold = fallback_threshold
        self.llm_request_timeout_seconds = llm_request_timeout_seconds

        self.rewriter = QueryRewriter(
            api_key,
            self.llm_config.base_url,
            self.llm_config.model,
            request_timeout_seconds=llm_request_timeout_seconds,
        )
        self.retrieval_pipe = RetrievalPipeline(
            qdrant_client,
            collection_name,
            hf_token,
            hf_embedding_model=hf_embedding_model,
            fastembed_cache_dir=fastembed_cache_dir,
        )
        self.reranker_pipe = RerankerPipeline(cache_dir=fastembed_cache_dir)

        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=self.llm_config.base_url,
            model=self.llm_config.model,
            temperature=0.1,
            timeout=llm_request_timeout_seconds,
            max_retries=1,
        )

        import os

        os.environ.setdefault("POLYRAG_WEB_SEARCH_TIMEOUT_SECONDS", str(web_search_timeout_seconds))

        self.gemini_client = None
        if genai is not None:
            try:
                import os

                gemini_key = os.environ.get("GEMINI_API_KEY")
                self.gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None
            except Exception as exc:
                logger.warning("Gemini judge disabled: %s", exc)

        self.dynamic_tools = [external_web_search, calculator]
        if enable_python_tool:
            self.dynamic_tools.append(run_python)
        self.model_with_tools = self.llm.bind_tools(self.dynamic_tools)

        self.workflow = StateGraph(AgentState)
        self._build_graph()

    def _call_gemini_judge(self, system_instruction: str, user_content: str) -> str:
        if not self.gemini_client or types is None:
            return "NO"
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
                    max_output_tokens=5,
                ),
            )
            text = getattr(response, "text", "") or ""
            return "YES" if "YES" in text.upper() else "NO"
        except Exception as exc:
            logger.warning("Gemini judge failed: %s", exc)
            return "NO"

    def _build_graph(self):
        def cache_judge_node(state: AgentState):
            if not state.get("context_cache"):
                return {"max_rerank_score": 0.0}

            user_msg = state["messages"][-1].content
            cache_sources = sorted({c.get("source", "unknown") for c in state["context_cache"]})
            sys_prompt = (
                "You are a strict validation judge. Determine if the user's incoming statement is a direct follow-up "
                "or question that can be answered entirely using the files currently cached in memory. "
                "Respond with EXACTLY 'YES' or 'NO' and absolutely nothing else."
            )
            user_prompt = f"Question: '{user_msg}'\nCached Documents: {cache_sources}"
            decision = self._call_gemini_judge(sys_prompt, user_prompt)

            if decision == "YES":
                cached_text = "\n\n".join([c.get("text", "") for c in state["context_cache"]])
                return {
                    "retrieved_context": cached_text,
                    "max_rerank_score": 1.0,
                    "citations": state["context_cache"],
                }
            return {"max_rerank_score": 0.0}

        def rewrite_judge_node(state: AgentState):
            user_msg = state["messages"][-1].content
            if len(state["messages"]) <= 1:
                return {"transformed_query": user_msg}

            sys_prompt = (
                "You are an information retrieval judge. Determine if the latest user question needs context "
                "from the chat history to be fully understood as a standalone query. Respond with EXACTLY 'YES' or 'NO'."
            )
            user_prompt = f"Latest Question: '{user_msg}'\nChat History Length: {len(state['messages']) - 1} turns."
            decision = self._call_gemini_judge(sys_prompt, user_prompt)
            return {"transformed_query": "__REWRITE_NEEDED__" if decision == "YES" else user_msg}

        def rewrite_exec_node(state: AgentState):
            user_msg = state["messages"][-1].content
            history = state["messages"][:-1]
            if state.get("ltm_summary"):
                history = [SystemMessage(content=f"Prior Summary: {state['ltm_summary']}")] + history
            return {"transformed_query": self.rewriter.run(user_msg, history)}

        def local_search_node(state: AgentState):
            query = state["transformed_query"]
            candidates = self.retrieval_pipe.run(
                query,
                top_k=self.retrieval_top_k,
                course_filter=state.get("course_filter"),
                degree_filter=state.get("degree_filter"),
                year_filter=state.get("year_filter"),
            )
            final_chunks = self.reranker_pipe.run(query, candidates, top_l=self.rerank_top_l)

            context_blocks, new_cache, max_score = [], [], 0.0
            for hit in final_chunks:
                payload = hit.payload or {}
                text_content = payload.get("text", "")
                source = str(payload.get("source", "unknown")).replace("\\", "/")
                filename = source.split("/")[-1]
                context_blocks.append(text_content)

                current_score = float(payload.get("rerank_score") or getattr(hit, "score", 0.0) or 0.0)
                max_score = max(max_score, current_score)
                new_cache.append(
                    {
                        "type": "local",
                        "source": filename,
                        "page": payload.get("index", "Unknown"),
                        "text": text_content,
                        "score": current_score,
                    }
                )

            citations_by_source = {}
            for citation in new_cache:
                source = citation["source"]
                existing = citations_by_source.setdefault(
                    source,
                    {
                        "type": "local",
                        "source": source,
                        "pages": set(),
                        "score": 0.0,
                    },
                )
                page = citation["page"]
                if page not in (None, "", "Unknown"):
                    existing["pages"].add(str(page))
                existing["score"] = max(existing["score"], float(citation.get("score") or 0.0))

            citations = []
            for item in citations_by_source.values():
                pages = sorted(item.pop("pages"), key=lambda value: (not value.isdigit(), value))
                item["page"] = ", ".join(pages) if pages else "Unknown"
                citations.append(item)

            return {
                "retrieved_context": "\n\n---\n\n".join(context_blocks),
                "max_rerank_score": max_score,
                "context_cache": new_cache,
                "citations": citations,
            }

        def web_search_fallback_node(state: AgentState):
            if not self.enable_web_fallback:
                return {}

            query = state["transformed_query"]
            web_raw_data = external_web_search.invoke({"query": query})
            web_citations = [{"type": "external", "source": f"Automatic web fallback: {query}"}]
            combined_context = (
                f"{state.get('retrieved_context', '')}\n\n"
                f"=== AUTOMATIC WEB FALLBACK CONTEXT ===\n{web_raw_data}"
            )
            return {
                "retrieved_context": combined_context,
                "citations": state.get("citations", []) + web_citations,
            }

        def agent_think_node(state: AgentState):
            ltm = state.get("ltm_summary", "No prior record summaries available.")
            context = state.get("retrieved_context") or "No relevant local context was retrieved."
            system_prompt = (
                "You are an advanced university study assistant for the user's Politecnico study material.\n"
                f"--- LONG TERM MEMORY SUMMARY ---\n{ltm}\n---------------------------------\n\n"
                "Use the retrieved context as the primary source. If the context is insufficient, say what is missing "
                "instead of inventing citations. You may call tools only when they materially improve the answer.\n\n"
                f"=== CURRENT RETRIEVED CONTEXT ===\n{context}\n"
            )
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = self.model_with_tools.invoke(messages)

            new_citations = list(state.get("citations", []))
            for call in getattr(response, "tool_calls", []) or []:
                if call.get("name") == "external_web_search":
                    query = call.get("args", {}).get("query", "")
                    new_citations.append({"type": "external", "source": f"Dynamic tool call: {query}"})
            return {"messages": [response], "citations": new_citations}

        def ltm_management_node(state: AgentState):
            messages = state["messages"]
            if len(messages) < 8:
                return {}

            messages_to_compress = messages[:-4]
            summary_prompt = (
                f"Progressively update this long-term conversation summary: '{state.get('ltm_summary', '')}'\n"
                f"Incorporate these older dialog turns without losing core technical context:\n{messages_to_compress}"
            )
            response = self.llm.invoke([HumanMessage(content=summary_prompt)])
            return {
                "ltm_summary": response.content.strip(),
                "messages": [RemoveMessage(id=m.id) for m in messages_to_compress],
            }

        self.workflow.add_node("cache_judge", cache_judge_node)
        self.workflow.add_node("rewrite_judge", rewrite_judge_node)
        self.workflow.add_node("rewrite_exec", rewrite_exec_node)
        self.workflow.add_node("local_search", local_search_node)
        self.workflow.add_node("web_search_fallback", web_search_fallback_node)
        self.workflow.add_node("agent_think", agent_think_node)
        self.workflow.add_node("execute_tools", ToolNode(self.dynamic_tools))
        self.workflow.add_node("ltm_compile", ltm_management_node)

        self.workflow.set_entry_point("cache_judge")
        self.workflow.add_conditional_edges(
            "cache_judge",
            lambda state: route_after_cache(state.get("max_rerank_score", 0.0)),
            {"agent_think": "agent_think", "rewrite_judge": "rewrite_judge"},
        )
        self.workflow.add_conditional_edges(
            "rewrite_judge",
            lambda state: route_after_rewrite(state.get("transformed_query", "")),
            {"rewrite_exec": "rewrite_exec", "local_search": "local_search"},
        )
        self.workflow.add_edge("rewrite_exec", "local_search")
        self.workflow.add_conditional_edges(
            "local_search",
            lambda state: route_after_search(state.get("max_rerank_score", 0.0), self.fallback_threshold),
            {"web_search_fallback": "web_search_fallback", "agent_think": "agent_think"},
        )
        self.workflow.add_edge("web_search_fallback", "agent_think")
        self.workflow.add_conditional_edges(
            "agent_think",
            lambda state: route_after_agent(state["messages"][-1]),
            {"tools": "execute_tools", "finish": "ltm_compile"},
        )
        self.workflow.add_edge("execute_tools", "agent_think")
        self.workflow.add_edge("ltm_compile", END)

        self.memory_saver = MemorySaver()
        self.agent_app = self.workflow.compile(checkpointer=self.memory_saver)
