"""SQLite-backed chat session and message history store."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.app.errors import NotFoundError


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SqliteSessionStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    thread_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    degree_filter TEXT,
                    year_filter TEXT,
                    course_filter TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    thread_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(thread_id) REFERENCES sessions(thread_id)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id, id)"
            )

    def create_session(
        self,
        *,
        title: str | None,
        mode: str = "general",
        degree_filter: str | None = None,
        year_filter: str | None = None,
        course_filter: str | None = None,
    ) -> dict[str, Any]:
        now = utc_now_iso()
        thread_id = str(uuid.uuid4())
        resolved_title = title or ("Course chat" if mode == "course" else "General chat")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (
                    thread_id, title, mode, degree_filter, year_filter, course_filter,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    thread_id,
                    resolved_title,
                    mode,
                    degree_filter,
                    year_filter,
                    course_filter,
                    now,
                    now,
                ),
            )
        return self.get_session(thread_id)

    def ensure_session(
        self,
        thread_id: str | None,
        *,
        title: str | None = None,
        mode: str = "general",
        degree_filter: str | None = None,
        year_filter: str | None = None,
        course_filter: str | None = None,
    ) -> dict[str, Any]:
        if thread_id:
            session = self.get_session(thread_id)
            self.update_session_context(
                thread_id,
                degree_filter=degree_filter,
                year_filter=year_filter,
                course_filter=course_filter,
            )
            return self.get_session(thread_id) if any([degree_filter, year_filter, course_filter]) else session
        return self.create_session(
            title=title,
            mode=mode,
            degree_filter=degree_filter,
            year_filter=year_filter,
            course_filter=course_filter,
        )

    def get_session(self, thread_id: str) -> dict[str, Any]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE thread_id = ?",
                (thread_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"Session '{thread_id}' was not found.")
        return dict(row)

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_session(self, thread_id: str) -> None:
        self.get_session(thread_id)
        with self._connect() as connection:
            connection.execute("DELETE FROM messages WHERE thread_id = ?", (thread_id,))
            connection.execute("DELETE FROM sessions WHERE thread_id = ?", (thread_id,))

    def update_session_context(
        self,
        thread_id: str,
        *,
        degree_filter: str | None = None,
        year_filter: str | None = None,
        course_filter: str | None = None,
    ) -> None:
        updates = {
            "degree_filter": degree_filter,
            "year_filter": year_filter,
            "course_filter": course_filter,
        }
        updates = {key: value for key, value in updates.items() if value is not None}
        if not updates:
            return

        assignments = ", ".join(f"{key} = ?" for key in updates)
        values = list(updates.values())
        values.extend([utc_now_iso(), thread_id])
        with self._connect() as connection:
            connection.execute(
                f"UPDATE sessions SET {assignments}, updated_at = ? WHERE thread_id = ?",
                values,
            )

    def add_message(
        self,
        thread_id: str,
        *,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.get_session(thread_id)
        now = utc_now_iso()
        payload = json.dumps(metadata or {}, ensure_ascii=False)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO messages (thread_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (thread_id, role, content, payload, now),
            )
            connection.execute(
                "UPDATE sessions SET updated_at = ? WHERE thread_id = ?",
                (now, thread_id),
            )
        return {
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": now,
        }

    def list_messages(self, thread_id: str, limit: int | None = None) -> list[dict[str, Any]]:
        self.get_session(thread_id)
        limit_clause = ""
        params: tuple[Any, ...] = (thread_id,)
        if limit is not None:
            limit_clause = "LIMIT ?"
            params = (thread_id, limit)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT role, content, metadata, created_at
                FROM (
                    SELECT role, content, metadata, created_at, id
                    FROM messages
                    WHERE thread_id = ?
                    ORDER BY id DESC
                    {limit_clause}
                )
                ORDER BY id ASC
                """,
                params,
            ).fetchall()
        messages = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item["metadata"] or "{}")
            messages.append(item)
        return messages
