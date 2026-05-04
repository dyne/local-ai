from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from local_ai.slices.documents.domain import ArchiveSource, DocumentRef, IndexRun


_SCHEMA_SQL = (
    """
    CREATE TABLE IF NOT EXISTS sources (
        id TEXT PRIMARY KEY,
        root_path TEXT NOT NULL UNIQUE,
        label TEXT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        include_globs_json TEXT NOT NULL DEFAULT '[]',
        exclude_globs_json TEXT NOT NULL DEFAULT '[]',
        enabled INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS document_refs (
        document_id TEXT PRIMARY KEY,
        source_id TEXT NOT NULL,
        path TEXT NOT NULL,
        title TEXT NULL,
        mime_type TEXT NULL,
        last_seen_at TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS index_runs (
        run_id TEXT PRIMARY KEY,
        started_at TEXT NOT NULL,
        finished_at TEXT NULL,
        status TEXT NOT NULL,
        rebuild INTEGER NOT NULL,
        stdout_tail TEXT NULL,
        stderr_tail TEXT NULL,
        error_message TEXT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS answer_runs (
        run_id TEXT PRIMARY KEY,
        query TEXT NOT NULL,
        created_at TEXT NOT NULL,
        lexical_candidate_count INTEGER NOT NULL,
        refined_passage_count INTEGER NOT NULL,
        generation_status TEXT NOT NULL,
        embedding_model TEXT NULL,
        generation_model TEXT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )
    """,
)


@dataclass(frozen=True)
class SqliteDocumentsRepository:
    """SQLite-backed local metadata repository for Documents slice."""

    db_path: Path

    def __post_init__(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            for statement in _SCHEMA_SQL:
                connection.execute(statement)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _utc_now() -> str:
        return datetime.utcnow().isoformat()

    def save_source(self, source: ArchiveSource) -> ArchiveSource:
        now = self._utc_now()
        normalized_path = str(Path(source.root_path))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sources (id, root_path, label, created_at, updated_at, include_globs_json, exclude_globs_json, enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(id) DO UPDATE SET
                    root_path=excluded.root_path,
                    label=excluded.label,
                    updated_at=excluded.updated_at
                """,
                (
                    source.source_id,
                    normalized_path,
                    source.label,
                    now,
                    now,
                    "[]",
                    "[]",
                ),
            )
        return ArchiveSource(source_id=source.source_id, root_path=normalized_path, label=source.label)

    def list_sources(self) -> tuple[ArchiveSource, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, root_path, label FROM sources WHERE enabled = 1 ORDER BY created_at ASC"
            ).fetchall()
        return tuple(
            ArchiveSource(
                source_id=row["id"],
                root_path=row["root_path"],
                label=row["label"],
            )
            for row in rows
        )

    def disable_source(self, source_id: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE sources SET enabled = 0, updated_at = ? WHERE id = ?", (self._utc_now(), source_id))

    def save_index_run(self, run: IndexRun) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO index_runs (run_id, started_at, finished_at, status, rebuild, stdout_tail, stderr_tail, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    finished_at=excluded.finished_at,
                    status=excluded.status,
                    rebuild=excluded.rebuild,
                    error_message=excluded.error_message
                """,
                (
                    run.run_id,
                    run.started_at.isoformat(),
                    run.finished_at.isoformat() if run.finished_at else None,
                    run.status,
                    1 if run.rebuild else 0,
                    None,
                    None,
                    run.error_message,
                ),
            )

    def get_index_run(self, run_id: str) -> IndexRun | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT run_id, started_at, finished_at, status, rebuild, error_message
                FROM index_runs
                WHERE run_id = ?
                """,
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        return IndexRun(
            run_id=row["run_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            status=row["status"],
            rebuild=bool(row["rebuild"]),
            error_message=row["error_message"],
        )

    def upsert_document_ref(self, document: DocumentRef) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO document_refs (document_id, source_id, path, title, mime_type, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    source_id=excluded.source_id,
                    path=excluded.path,
                    title=excluded.title,
                    mime_type=excluded.mime_type,
                    last_seen_at=excluded.last_seen_at
                """,
                (
                    document.document_id,
                    document.source_id,
                    document.source_path,
                    document.title,
                    document.mime_type,
                    self._utc_now(),
                ),
            )

    def get_document_ref(self, document_id: str) -> DocumentRef | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT document_id, source_id, path, title, mime_type
                FROM document_refs
                WHERE document_id = ?
                """,
                (document_id,),
            ).fetchone()
        if row is None:
            return None
        return DocumentRef(
            document_id=row["document_id"],
            source_id=row["source_id"],
            source_path=row["path"],
            title=row["title"],
            mime_type=row["mime_type"],
        )

    def set_setting(self, key: str, value: object) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, json.dumps(value)),
            )

    def get_setting(self, key: str) -> object | None:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return None
        return json.loads(row["value"])
