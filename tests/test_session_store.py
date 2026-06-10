from src.app.session_store import SqliteSessionStore


def test_session_store_persists_history(tmp_path):
    store = SqliteSessionStore(tmp_path / "sessions.sqlite")
    session = store.create_session(
        title="Data Science",
        mode="course",
        degree_filter="Magistrale",
        year_filter="Primo Anno",
        course_filter="Data Science",
    )

    store.add_message(session["thread_id"], role="user", content="What is clustering?")
    store.add_message(
        session["thread_id"],
        role="assistant",
        content="Clustering groups similar records.",
        metadata={"query_used": "clustering"},
    )

    messages = store.list_messages(session["thread_id"])
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[1]["metadata"]["query_used"] == "clustering"


def test_session_store_limits_and_deletes_history(tmp_path):
    store = SqliteSessionStore(tmp_path / "sessions.sqlite")
    session = store.create_session(title="General", mode="general")

    for index in range(5):
        store.add_message(session["thread_id"], role="user", content=f"message {index}")

    limited = store.list_messages(session["thread_id"], limit=2)
    assert [message["content"] for message in limited] == ["message 3", "message 4"]

    store.delete_session(session["thread_id"])
    assert store.list_sessions() == []
