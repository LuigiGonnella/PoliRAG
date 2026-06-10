"""FastAPI entrypoint for the PoliRAG microservice."""
from __future__ import annotations

import json

from fastapi import FastAPI, Query, Response
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from src.app.errors import AppError
from src.app.rag_service import RAGService
from src.app.schemas import (
    AgentChatPayload,
    AgentChatResponse,
    ChatHistoryResponse,
    CourseCatalogResponse,
    ErrorResponse,
    HealthResponse,
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
)
from src.app.session_store import SqliteSessionStore
from src.app.settings import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.session_store = SqliteSessionStore(settings.session_db_path)
    app.state.rag_service = RAGService(
        settings=settings,
        session_store=app.state.session_store,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.error, detail=exc.detail).model_dump(),
        )

    @app.get("/health", response_model=HealthResponse)
    async def health():
        return await run_in_threadpool(app.state.rag_service.health)

    @app.get(f"{settings.api_prefix}/courses", response_model=CourseCatalogResponse)
    async def list_courses(refresh: bool = Query(default=False)):
        return await run_in_threadpool(app.state.rag_service.course_catalog.get_catalog, refresh=refresh)

    @app.post(f"{settings.api_prefix}/sessions", response_model=SessionResponse)
    async def create_session(payload: SessionCreateRequest):
        return await run_in_threadpool(
            app.state.session_store.create_session,
            title=payload.title,
            mode=payload.mode,
            degree_filter=payload.degree_filter,
            year_filter=payload.year_filter,
            course_filter=payload.course_filter,
        )

    @app.get(f"{settings.api_prefix}/sessions", response_model=SessionListResponse)
    async def list_sessions():
        sessions = await run_in_threadpool(app.state.session_store.list_sessions)
        return {"sessions": sessions}

    @app.get(f"{settings.api_prefix}/sessions/{{thread_id}}", response_model=ChatHistoryResponse)
    async def get_session(thread_id: str):
        session = await run_in_threadpool(app.state.session_store.get_session, thread_id)
        messages = await run_in_threadpool(app.state.session_store.list_messages, thread_id)
        return {"session": session, "messages": messages}

    @app.get(f"{settings.api_prefix}/sessions/{{thread_id}}/messages", response_model=ChatHistoryResponse)
    async def get_session_messages(thread_id: str):
        return await get_session(thread_id)

    @app.delete(f"{settings.api_prefix}/sessions/{{thread_id}}", status_code=204)
    async def delete_session(thread_id: str):
        await run_in_threadpool(app.state.session_store.delete_session, thread_id)
        return Response(status_code=204)

    @app.post(f"{settings.api_prefix}/agent/chat", response_model=AgentChatResponse)
    async def execute_agent_loop(payload: AgentChatPayload):
        return await run_in_threadpool(app.state.rag_service.chat, payload)

    @app.post(f"{settings.api_prefix}/agent/chat/stream")
    async def stream_agent_loop(payload: AgentChatPayload):
        def event_stream():
            try:
                for event in app.state.rag_service.stream_chat_events(payload):
                    yield json.dumps(event, ensure_ascii=False) + "\n"
            except Exception as exc:
                yield json.dumps({"event": "error", "message": str(exc)}, ensure_ascii=False) + "\n"

        return StreamingResponse(event_stream(), media_type="application/x-ndjson")

    if settings.frontend_dir.exists():
        app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")

    return app


app = create_app()
