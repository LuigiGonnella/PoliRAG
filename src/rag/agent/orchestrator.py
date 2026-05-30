import os
import requests
from typing import Annotated, TypedDict, List
from qdrant_client import QdrantClient

# LangGraph Core Primitives
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage

from langchain_openai import ChatOpenAI
from google import genai
from google.genai import types

from src.rag.query_transform.query_rewriter import QueryRewriter
from src.rag.retrieval.retrieval_pipeline import RetrievalPipeline
from src.rag.reranking.reranker_pipeline import RerankerPipeline
from src.rag.agent.tools import external_web_search, calculator, run_python


# ---------------------------------------------------------------------------
# GRAPH STATE SPECIFICATION
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    transformed_query: str
    course_filter: str
    degree_filter: str
    retrieved_context: str
    context_cache: List[dict]
    ltm_summary: str
    max_rerank_score: float
    citations: List[dict]

class PolyRAGAgent:
    def __init__(self, qdrant_client: QdrantClient, collection_name: str, hf_token: str, llm_config: dict):
        self.hf_token = hf_token
        self.rewriter = QueryRewriter(llm_config["key"], llm_config["base_url"], llm_config["model"])
        self.retrieval_pipe = RetrievalPipeline(qdrant_client, collection_name, hf_token)
        self.reranker_pipe = RerankerPipeline()
        
        # Core Orchestration Agent (DeepSeek via OpenRouter)
        self.llm = ChatOpenAI(api_key=llm_config["key"], base_url=llm_config["base_url"], model=llm_config["model"], temperature=0.1)
        
        # Free Cloud Evaluator (Gemini 2.5 Flash Lite)
        gemini_key = os.environ.get("GEMINI_API_KEY")
        self.gemini_client = genai.Client(api_key=gemini_key) if gemini_key else None

        # Dynamic Tools Configuration Layer
        self.dynamic_tools = [external_web_search, calculator, run_python]
        self.model_with_tools = self.llm.bind_tools(self.dynamic_tools)
        
        self.workflow = StateGraph(AgentState)
        self._build_graph()
    
    def _call_gemini_judge(self, system_instruction: str, user_content: str) -> str:
        """Helper to run low-latency binary classification tasks using Gemini."""
        if not self.gemini_client:
            print("Warning: GEMINI_API_KEY is missing. Defaulting evaluation gate to 'NO'.")
            return "NO"
        try:
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
                    max_output_tokens=5
                )
            )
            return "YES" if "YES" in response.text.upper() else "NO"
        except Exception as e:
            print(f"Gemini Judge Exception: {e}. Falling back to 'NO'.")
            return "NO"

    def _build_graph(self):
        
        # NODE 1: Gemini Context Cache Judge
        def cache_judge_node(state: AgentState):
            if not state.get("context_cache"):
                return {"max_rerank_score": 0.0}
            
            user_msg = state["messages"][-1].content
            cache_sources = [c["source"] for c in state["context_cache"]]
            
            sys_prompt = (
                "You are a strict validation judge. Determine if the user's incoming statement is a direct follow-up "
                "or question that can be answered entirely using the files currently cached in memory. "
                "Respond with EXACTLY 'YES' or 'NO' and absolutely nothing else."
            )
            user_prompt = f"Question: '{user_msg}'\nCached Documents: {cache_sources}"
            
            decision = self._call_gemini_judge(sys_prompt, user_prompt)
            
            if decision == "YES":
                # BYPASS SEARCH: Inject cached text block segments straight to state
                cached_text = "\n\n".join([c["text"] for c in state["context_cache"]])
                return {
                    "retrieved_context": cached_text,
                    "max_rerank_score": 1.0, # Sentinel value to signal bypass routing edge
                    "citations": state["context_cache"]
                }
            return {"max_rerank_score": 0.0}

        # NODE 2: Gemini Query Transformation Judge
        def rewrite_judge_node(state: AgentState):
            user_msg = state["messages"][-1].content
            
            # If there is no previous chat history, a rewrite is never needed
            if len(state["messages"]) <= 1:
                return {"transformed_query": user_msg}
                
            sys_prompt = (
                "You are an information retrieval judge. Determine if the latest user question needs context "
                "from the chat history to be fully understood as a standalone query (e.g., uses pronouns like 'it', "
                "'this', 'that', 'his algorithm'). Respond with EXACTLY 'YES' or 'NO'."
            )
            user_prompt = f"Latest Question: '{user_msg}'\nChat History Length: {len(state['messages'])-1} turns."
            
            decision = self._call_gemini_judge(sys_prompt, user_prompt)
            
            if decision == "YES":
                return {"transformed_query": "__REWRITE_NEEDED__"} # Routing execution flag
            return {"transformed_query": user_msg}

        # NODE 3: Query Transformation Execution Node
        def rewrite_exec_node(state: AgentState):
            user_msg = state["messages"][-1].content
            history = state["messages"][:-1]
            if state.get("ltm_summary"):
                history = [SystemMessage(content=f"Prior Summary: {state['ltm_summary']}")] + history
            
            rewritten = self.rewriter.run(user_msg, history)
            return {"transformed_query": rewritten}

        # NODE 4: Two-Stage Local Search
        def local_search_node(state: AgentState):
            query = state["transformed_query"]
            candidates = self.retrieval_pipe.run(
                query, top_k=25, 
                course_filter=state.get("course_filter"), degree_filter=state.get("degree_filter")
            )
            final_chunks = self.reranker_pipe.run(query, candidates, top_l=5)
            
            context_blocks, new_cache, max_score = [], [], 0.0
            for hit in final_chunks:
                text_content = hit.payload.get("text", "")
                filename = hit.payload.get("source", "").replace("\\", "/").split("/")[-1]
                context_blocks.append(text_content)
                
                current_score = getattr(hit, 'score', 0.0) or hit.payload.get("score", 0.0)
                if current_score > max_score:
                    max_score = current_score
                
                new_cache.append({
                    "type": "local", "source": filename, "page": hit.payload.get("index", "Unknown"), "text": text_content
                })

            return {
                "retrieved_context": "\n\n---\n\n".join(context_blocks),
                "max_rerank_score": max_score,
                "context_cache": new_cache,
                "citations": [{"type": "local", "source": c["source"], "page": c["page"]} for c in new_cache]
            }

        # NODE 5: Deterministic Web Fallback Node (Executed automatically if Score < 0.45)
        def web_search_fallback_node(state: AgentState):
            query = state["transformed_query"]
            # Call tool inline programmatically
            web_raw_data = external_web_search.invoke(query)
            
            web_citations = [{"type": "external", "source": f"Automatic Web Fallback: '{query}'"}]
            combined_context = f"{state['retrieved_context']}\n\n=== AUTOMATIC WEB FALLBACK CONTEXT ===\n{web_raw_data}"
            
            return {
                "retrieved_context": combined_context,
                "citations": state["citations"] + web_citations
            }

        # NODE 6: Dynamic Agent Decision Core Execution
        def agent_think_node(state: AgentState):
            ltm = state.get("ltm_summary", "No prior record summaries available.")
            system_prompt = (
                "You are an advanced university study assistant agent.\n"
                f"--- LONG TERM MEMORY SUMMARY ---\n{ltm}\n---------------------------------\n\n"
                "Review the context material below to answer the user query. "
                "You have access to dynamic tools (calculator, run_python, external_web_search) "
                "which you can call if you need to run calculations, test snippets, or research extra details.\n\n"
                f"=== CURRENT RETRIEVED CONTEXT ===\n{state['retrieved_context']}\n"
            )
            messages = [SystemMessage(content=system_prompt)] + state["messages"]
            response = self.model_with_tools.invoke(messages)
            
            # Extract on-the-fly tool invocations for citations arrays
            new_citations = list(state.get("citations", []))
            if hasattr(response, "tool_calls") and response.tool_calls:
                for call in response.tool_calls:
                    if call["name"] == "external_web_search":
                        new_citations.append({
                            "type": "external", "source": f"Dynamic Tool Call: '{call['args'].get('query')}'"
                        })
            return {"messages": [response], "citations": new_citations}

        # NODE 7: Long-Term Memory Compactor
        def ltm_management_node(state: AgentState):
            messages = state["messages"]
            if len(messages) < 8:
                return {}
            summary_prompt = f"Update this summary: {state.get('ltm_summary', '')}\nWith these messages:\n{messages[-4:]}"
            response = self.llm.invoke([HumanMessage(content=summary_prompt)])
            return {"ltm_summary": response.content.strip(), "messages": [RemoveMessage(id=m.id) for m in messages[:-4]]}

        # ---------------------------------------------------------------------------
        # GRAPH SYSTEM EDGE ROUTING GRAPH
        # ---------------------------------------------------------------------------
        self.workflow.add_node("cache_judge", cache_judge_node)
        self.workflow.add_node("rewrite_judge", rewrite_judge_node)
        self.workflow.add_node("rewrite_exec", rewrite_exec_node)
        self.workflow.add_node("local_search", local_search_node)
        self.workflow.add_node("web_search_fallback", web_search_fallback_node)
        self.workflow.add_node("agent_think", agent_think_node)
        self.workflow.add_node("execute_tools", ToolNode(self.dynamic_tools))
        self.workflow.add_node("ltm_compile", ltm_management_node)

        # Set Entry Point Flow
        self.workflow.set_entry_point("cache_judge")

        # Edge 1: Cache Judge Conditional Router
        self.workflow.add_conditional_edges(
            "cache_judge",
            lambda s: "agent_think" if s["max_rerank_score"] >= 1.0 else "rewrite_judge",
            {"agent_think": "agent_think", "rewrite_judge": "rewrite_judge"}
        )

        # Edge 2: Rewrite Judge Conditional Router
        self.workflow.add_conditional_edges(
            "rewrite_judge",
            lambda s: "rewrite_exec" if s["transformed_query"] == "__REWRITE_NEEDED__" else "local_search",
            {"rewrite_exec": "rewrite_exec", "local_search": "local_search"}
        )
        self.workflow.add_edge("rewrite_exec", "local_search")

        # Edge 3: Deterministic Low Score Fallback Router
        self.workflow.add_conditional_edges(
            "local_search",
            lambda s: "web_search_fallback" if s["max_rerank_score"] < 0.45 else "agent_think",
            {"web_search_fallback": "web_search_fallback", "agent_think": "agent_think"}
        )
        self.workflow.add_edge("web_search_fallback", "agent_think")

        # Edge 4: Dynamic Tool-Execution Loopback Engine
        self.workflow.add_conditional_edges(
            "agent_think",
            lambda s: "tools" if (hasattr(s["messages"][-1], "tool_calls") and s["messages"][-1].tool_calls) else "finish",
            {"tools": "execute_tools", "finish": "ltm_compile"}
        )
        self.workflow.add_edge("execute_tools", "agent_think")
        self.workflow.add_edge("ltm_compile", END)

        self.memory_saver = MemorySaver()
        self.agent_app = self.workflow.compile(checkpointer=self.memory_saver)