"""Runtime settings for the PoliRAG API service."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Polyhedric"
    environment: str = "development"
    api_prefix: str = "/v1"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "uni_docs"

    llm_api_key: str | None = None
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "deepseek/deepseek-v4-pro"
    gemini_api_key: str | None = None
    tavily_api_key: str | None = None
    hf_api_token: str | None = None
    hf_embedding_model: str = "BAAI/bge-small-en-v1.5"
    fastembed_cache_dir: Path = Path("data/fastembed_cache")

    frontend_dir: Path = Path("frontend/dist")
    session_db_path: Path = Path("data/app_sessions.sqlite")

    cors_origins: str = (
        "http://localhost:8000,http://127.0.0.1:8000,"
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    retrieval_top_k: int = 25
    rerank_top_l: int = 10
    rerank_fallback_threshold: float = 0.45
    agent_response_timeout_seconds: int = 180
    llm_request_timeout_seconds: int = 60
    web_search_timeout_seconds: int = 12
    enable_web_fallback: bool = True
    enable_python_tool: bool = False
    course_catalog_ttl_seconds: int = 300
    max_history_messages: int = 16
    auto_create_payload_indexes: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def agent_ready(self) -> bool:
        return bool(self.llm_api_key and self.qdrant_url)

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
