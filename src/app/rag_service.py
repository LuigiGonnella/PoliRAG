"""Service facade around Qdrant, course metadata, and the LangGraph agent."""
from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from qdrant_client import QdrantClient, models

from src.app.course_catalog import CourseCatalogService
from src.app.errors import AgentExecutionError, ConfigurationError
from src.app.schemas import AgentChatPayload
from src.app.session_store import SqliteSessionStore
from src.app.settings import Settings
from src.rag.agent.llm_config import LLMConfig


class RAGService:
    def __init__(self, *, settings: Settings, session_store: SqliteSessionStore):
        self.settings = settings
        self.session_store = session_store
        self._qdrant_client: QdrantClient | None = None
        self._agent = None
        self._course_catalog: CourseCatalogService | None = None
        self._payload_indexes_ready = False
        self._chat_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="polyrag-chat")

    @property
    def qdrant_client(self) -> QdrantClient:
        if self._qdrant_client is None:
            self._qdrant_client = QdrantClient(
                url=self.settings.qdrant_url,
                api_key=self.settings.qdrant_api_key,
            )
        return self._qdrant_client

    @property
    def course_catalog(self) -> CourseCatalogService:
        if self._course_catalog is None:
            self._course_catalog = CourseCatalogService(
                client=self.qdrant_client,
                collection_name=self.settings.qdrant_collection,
                ttl_seconds=self.settings.course_catalog_ttl_seconds,
            )
        return self._course_catalog

    @property
    def agent(self):
        if self._agent is None:
            if not self.settings.llm_api_key:
                raise ConfigurationError("LLM_API_KEY is required before the agent can answer chat requests.")

            if self.settings.hf_api_token:
                os.environ.setdefault("HF_TOKEN", self.settings.hf_api_token)
            if self.settings.tavily_api_key:
                os.environ.setdefault("TAVILY_API_KEY", self.settings.tavily_api_key)
            os.environ.setdefault(
                "POLYRAG_WEB_SEARCH_TIMEOUT_SECONDS",
                str(self.settings.web_search_timeout_seconds),
            )

            self.ensure_payload_indexes()

            from src.rag.agent.orchestrator import PolyRAGAgent

            llm_config = LLMConfig(
                key=self.settings.llm_api_key,
                base_url=self.settings.llm_base_url,
                model=self.settings.llm_model,
            )
            self._agent = PolyRAGAgent(
                qdrant_client=self.qdrant_client,
                collection_name=self.settings.qdrant_collection,
                hf_token=self.settings.hf_api_token,
                llm_config=llm_config,
                hf_embedding_model=self.settings.hf_embedding_model,
                fastembed_cache_dir=str(self.settings.fastembed_cache_dir),
                llm_request_timeout_seconds=self.settings.llm_request_timeout_seconds,
                web_search_timeout_seconds=self.settings.web_search_timeout_seconds,
                enable_web_fallback=self.settings.enable_web_fallback,
                enable_python_tool=self.settings.enable_python_tool,
                retrieval_top_k=self.settings.retrieval_top_k,
                rerank_top_l=self.settings.rerank_top_l,
                fallback_threshold=self.settings.rerank_fallback_threshold,
            )
        return self._agent

    def health(self) -> dict[str, Any]:
        details: dict[str, Any] = {}
        qdrant_ok = False
        try:
            qdrant_ok = self.qdrant_client.collection_exists(self.settings.qdrant_collection)
        except Exception as exc:
            details["qdrant_error"] = str(exc)

        return {
            "status": "ok" if qdrant_ok and self.settings.agent_ready else "degraded",
            "qdrant": qdrant_ok,
            "collection": self.settings.qdrant_collection,
            "agent_ready": self.settings.agent_ready,
            "details": details,
        }

    def ensure_payload_indexes(self) -> None:
        if self._payload_indexes_ready or not self.settings.auto_create_payload_indexes:
            return

        for field_name in ("course", "year", "degree_level"):
            try:
                self.qdrant_client.create_payload_index(
                    collection_name=self.settings.qdrant_collection,
                    field_name=field_name,
                    field_schema=models.PayloadSchemaType.KEYWORD,
                    wait=True,
                )
            except Exception as exc:
                message = str(exc).lower()
                if "already exists" not in message and "exists" not in message:
                    raise

        self._payload_indexes_ready = True

    def _load_conversation_window(self, thread_id: str):
        stored_messages = self.session_store.list_messages(
            thread_id,
            limit=self.settings.max_history_messages,
        )
        messages = []
        for item in stored_messages:
            role = item["role"]
            content = item["content"]
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            elif role == "system":
                messages.append(SystemMessage(content=content))
        return messages

    @staticmethod
    def dedupe_citations(citations: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: dict[tuple[str, str], dict[str, Any]] = {}
        for citation in citations:
            citation_type = str(citation.get("type") or "local")
            source = str(citation.get("source") or "source")
            key = (citation_type, source)
            current = deduped.setdefault(key, {**citation, "type": citation_type, "source": source})

            page = citation.get("page")
            if page and page != "Unknown":
                pages = set(str(current.get("page", "")).split(", ")) if current.get("page") else set()
                pages.add(str(page))
                current["page"] = ", ".join(sorted(page for page in pages if page))

            score = float(citation.get("score") or 0.0)
            if score > float(current.get("score") or 0.0):
                current["score"] = score
        return list(deduped.values())

    def chat(self, payload: AgentChatPayload) -> dict[str, Any]:
        session = self.session_store.ensure_session(
            payload.thread_id,
            mode="course" if payload.course_filter else "general",
            degree_filter=payload.degree_filter,
            year_filter=payload.year_filter,
            course_filter=payload.course_filter,
        )
        thread_id = session["thread_id"]
        history_messages = self._load_conversation_window(thread_id)
        self.session_store.add_message(thread_id, role="user", content=payload.message)

        config = {"configurable": {"thread_id": f"{thread_id}:{len(history_messages)}"}}
        initial_input: dict[str, Any] = {
            "messages": [*history_messages, HumanMessage(content=payload.message)],
        }

        if payload.course_filter:
            initial_input["course_filter"] = payload.course_filter
        if payload.year_filter:
            initial_input["year_filter"] = payload.year_filter
        if payload.degree_filter:
            initial_input["degree_filter"] = payload.degree_filter

        try:
            self.ensure_payload_indexes()
            output_state = self.agent.agent_app.invoke(initial_input, config=config)
        except ConfigurationError:
            raise
        except Exception as exc:
            raise AgentExecutionError(str(exc)) from exc

        final_answer = output_state["messages"][-1].content
        response = {
            "thread_id": thread_id,
            "answer": final_answer,
            "citations": self.dedupe_citations(output_state.get("citations", [])),
            "ltm_summary_status": "Active" if output_state.get("ltm_summary") else "None",
            "query_used": output_state.get("transformed_query", payload.message),
        }
        self.session_store.add_message(
            thread_id,
            role="assistant",
            content=final_answer,
            metadata={
                "citations": response["citations"],
                "query_used": response["query_used"],
                "ltm_summary_status": response["ltm_summary_status"],
            },
        )
        return response

    def stream_chat_events(self, payload: AgentChatPayload):
        yield {"event": "status", "message": "Retrieving sources"}
        started_at = time.monotonic()
        future = self._chat_executor.submit(self.chat, payload)
        while True:
            try:
                response = future.result(timeout=5)
                break
            except TimeoutError:
                elapsed = time.monotonic() - started_at
                if elapsed >= self.settings.agent_response_timeout_seconds:
                    future.cancel()
                    yield {
                        "event": "error",
                        "message": (
                            "The answer timed out while waiting for the RAG pipeline or Tavily web search. "
                            "Try again with a narrower question, or increase AGENT_RESPONSE_TIMEOUT_SECONDS."
                        ),
                    }
                    return
                yield {"event": "status", "message": "Still working on the answer"}

        yield {
            "event": "metadata",
            "thread_id": response["thread_id"],
            "query_used": response["query_used"],
            "ltm_summary_status": response["ltm_summary_status"],
        }
        for character in response["answer"]:
            yield {"event": "delta", "text": character}
            time.sleep(0.002)
        yield {
            "event": "done",
            "thread_id": response["thread_id"],
            "citations": response["citations"],
        }
