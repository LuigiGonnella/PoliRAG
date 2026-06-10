"""Pydantic request and response models for the PoliRAG API."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ChatMode = Literal["general", "course"]
MessageRole = Literal["user", "assistant", "system"]


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    qdrant: bool
    collection: str
    agent_ready: bool
    details: dict[str, Any] = Field(default_factory=dict)


class CourseOption(BaseModel):
    label: str
    value: str
    degree: str
    year: str


class YearOption(BaseModel):
    label: str
    value: str
    courses: list[CourseOption] = Field(default_factory=list)


class DegreeOption(BaseModel):
    label: str
    value: str
    years: list[YearOption] = Field(default_factory=list)


class CourseCatalogResponse(BaseModel):
    source: Literal["qdrant", "static", "empty"]
    degrees: list[DegreeOption] = Field(default_factory=list)


class SessionCreateRequest(BaseModel):
    mode: ChatMode = "general"
    title: str | None = Field(default=None, max_length=120)
    degree_filter: str | None = None
    year_filter: str | None = None
    course_filter: str | None = None


class SessionResponse(BaseModel):
    thread_id: str
    title: str
    mode: ChatMode
    degree_filter: str | None = None
    year_filter: str | None = None
    course_filter: str | None = None
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatHistoryResponse(BaseModel):
    session: SessionResponse
    messages: list[ChatMessage]


class AgentChatPayload(BaseModel):
    thread_id: str | None = None
    message: str = Field(min_length=1)
    course_filter: str | None = None
    year_filter: str | None = None
    degree_filter: str | None = None


class AgentChatResponse(BaseModel):
    thread_id: str
    answer: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    ltm_summary_status: Literal["Active", "None"] = "None"
    query_used: str
