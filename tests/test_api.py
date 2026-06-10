from fastapi.testclient import TestClient

from src.app.app import create_app
from src.app.schemas import CourseCatalogResponse
from src.app.settings import Settings


class FakeCatalog:
    def get_catalog(self, refresh=False):
        return CourseCatalogResponse(source="empty", degrees=[])


class FakeRAGService:
    def __init__(self):
        self.course_catalog = FakeCatalog()

    def health(self):
        return {
            "status": "ok",
            "qdrant": True,
            "collection": "uni_docs",
            "agent_ready": True,
            "details": {},
        }

    def chat(self, payload):
        return {
            "thread_id": payload.thread_id or "fake-thread",
            "answer": "Mock answer",
            "citations": [{"type": "local", "source": "mock.pdf", "page": 1}],
            "ltm_summary_status": "None",
            "query_used": payload.message,
        }

    def stream_chat_events(self, payload):
        yield {"event": "metadata", "thread_id": payload.thread_id or "fake-thread"}
        yield {"event": "delta", "text": "M"}
        yield {"event": "delta", "text": "D"}
        yield {"event": "done", "thread_id": payload.thread_id or "fake-thread", "citations": []}


def make_client(tmp_path):
    settings = Settings(
        qdrant_url="http://testserver:6333",
        llm_api_key="test-key",
        session_db_path=tmp_path / "sessions.sqlite",
        frontend_dir=tmp_path / "missing-frontend",
    )
    app = create_app(settings)
    app.state.rag_service = FakeRAGService()
    return TestClient(app)


def test_settings_accept_comma_separated_cors_origins():
    settings = Settings(cors_origins="http://localhost:8000,http://127.0.0.1:5173")
    assert settings.cors_origin_list == [
        "http://localhost:8000",
        "http://127.0.0.1:5173",
    ]


def test_health_endpoint(tmp_path):
    client = make_client(tmp_path)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["qdrant"] is True


def test_session_and_history_endpoints(tmp_path):
    client = make_client(tmp_path)
    created = client.post("/v1/sessions", json={"mode": "general", "title": "Exam prep"})
    assert created.status_code == 200
    thread_id = created.json()["thread_id"]

    listed = client.get("/v1/sessions")
    assert listed.status_code == 200
    assert listed.json()["sessions"][0]["thread_id"] == thread_id

    history = client.get(f"/v1/sessions/{thread_id}")
    assert history.status_code == 200
    assert history.json()["messages"] == []

    deleted = client.delete(f"/v1/sessions/{thread_id}")
    assert deleted.status_code == 204
    assert client.get(f"/v1/sessions/{thread_id}").status_code == 404


def test_chat_endpoint(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/v1/agent/chat", json={"message": "What is BM25?"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Mock answer"


def test_stream_chat_endpoint(tmp_path):
    client = make_client(tmp_path)
    response = client.post("/v1/agent/chat/stream", json={"message": "What is BM25?"})
    assert response.status_code == 200
    assert '"event": "delta"' in response.text
    assert '"text": "M"' in response.text
