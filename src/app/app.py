import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client import models
from openai import OpenAI
from retrieval.retrieval_pipeline import RetrievalPipeline
from reranking.reranker_pipeline import RerankerPipeline

app = FastAPI(title="PoliRAG Agent API")

# Enable CORS to connect frontend to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------------------------------------------------------------------
# INITIALIZE CLOUD APIS & CONFIGURATIONS
# ---------------------------------------------------------------------------
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")
COLLECTION_NAME = "uni_docs"

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")

# OPENROUTER
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek/deepseek-v4-pro")

# Instantiate Clients
qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
llm_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)

# Instantiate pipelines globally so they don't reload models on every request
retrieval_pipe = RetrievalPipeline(qdrant_client, COLLECTION_NAME, HF_API_TOKEN)
reranker_pipe = RerankerPipeline()

# ---------------------------------------------------------------------------
# DATA SCHEMAS
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    course_filter: str = None       # Optional: e.g., "Chimica"
    degree_filter: str = None       # Optional: e.g., "Triennale"

# ---------------------------------------------------------------------------
# CHAT ENDPOINT (READ ONLY)
# ---------------------------------------------------------------------------
@app.post("/chat")
async def chat_with_agent(request: ChatRequest):
    try:
        # STAGE 1: Extract Top-K broad search candidates via Hybrid Search
        candidates = retrieval_pipe.run(
            query=request.message,
            top_k=20,  # Retrieve a broad set of candidates first
            course_filter=request.course_filter,
            degree_filter=request.degree_filter
        )
        
        # STAGE 2: Deep Context Re-ranking down to Top-L high-quality chunks
        final_chunks = reranker_pipe.run(
            query=request.message,
            candidates=candidates,
            top_l=5    # Keep only the top 5 most relevant chunks for the LLM
        )

        # Build context blocks and construct citations array simultaneously
        context_blocks = []
        citations = []
        
        for hit in final_chunks:
            payload = hit.payload
            context_blocks.append(payload.get("text", ""))
            
            # Extract file path string safely across OS differences
            source_path = payload.get("source", "Unknown")
            filename = source_path.replace("\\", "/").split("/")[-1]
            
            citation_info = {
                "source": filename,
                "page": payload.get("index", "Unknown"),
                "course": payload.get("course", "Unknown")
            }
            
            # Prevent adding duplicate citations if multiple chunks originate from the same page
            if citation_info not in citations:
                citations.append(citation_info)

        context_str = "\n\n---\n\n".join(context_blocks)

        # Execute LLM prompt with context injection
        system_prompt = (
            "You are an expert university study assistant. Answer the user's questions accurately "
            "based strictly on the provided context extracted from their course notes.\n\n"
            f"=== CONTEXT FROM UNIVERSITY NOTES ===\n{context_str}\n========================="
        )

        response = llm_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.3  # Lower temperature ensures stricter adherence to context
        )

        # Return response alongside clean, structured references
        return {
            "answer": response.choices[0].message.content,
            "citations": citations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))