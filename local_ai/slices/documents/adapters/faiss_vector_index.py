from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import sqlite3
from threading import RLock
from pathlib import Path
from typing import Any

import numpy as np

from local_ai.slices.documents.domain import EvidencePassage, Passage


class FaissUnavailableError(RuntimeError):
    """Raised when FAISS dependency is unavailable."""


@dataclass
class FaissVectorSearchIndex:
    """Local FAISS vector index with SQLite metadata sidecar."""

    index_path: Path
    metadata_db_path: Path

    def __post_init__(self) -> None:
        self.index_path = Path(self.index_path)
        self.metadata_db_path = Path(self.metadata_db_path)
        self._lock = RLock()
        self._faiss: Any | None = None
        self._faiss_error: str | None = None
        self._index: Any | None = None
        self._dimension: int | None = None
        self._model_id: str | None = None
        self._init_faiss()

    def _init_faiss(self) -> None:
        try:
            import faiss  # type: ignore

            self._faiss = faiss
            self._faiss_error = None
        except Exception as exc:  # pragma: no cover - environment dependent
            self._faiss = None
            self._faiss_error = str(exc)

    def ensure_index(self, *, dimension: int, model_id: str) -> None:
        if dimension <= 0:
            raise ValueError("Vector dimension must be positive.")
        with self._lock:
            self._require_faiss()
            self._ensure_paths()
            self._ensure_schema()
            stored_state = self._load_state()
            reset_required = (
                stored_state is not None
                and (stored_state["dimension"] != dimension or stored_state["embedding_model"] != model_id)
            )
            if reset_required:
                self._reset_storage()
            self._dimension = dimension
            self._model_id = model_id
            self._store_state(dimension=dimension, model_id=model_id)
            self._load_or_create_faiss_index(dimension)

    def upsert_passages(self, passages, vectors) -> None:
        if len(passages) != len(vectors):
            raise ValueError("Passage and vector counts must match.")
        with self._lock:
            if self._index is None or self._dimension is None or self._model_id is None:
                raise ValueError("Vector index must be ensured before upsert.")

            matrix = np.asarray(vectors, dtype=np.float32)
            if matrix.ndim != 2 or matrix.shape[1] != self._dimension:
                raise ValueError("Vector dimension mismatch during upsert.")
            normalized = _normalize_rows(matrix)

            conn = self._connect()
            try:
                for passage, row in zip(passages, normalized):
                    vector_id = self._vector_id_for_passage(passage.passage_id)
                    self._remove_vector_if_exists(conn, passage.passage_id, vector_id)
                    self._upsert_metadata(conn, passage, vector_id)
                    ids = np.asarray([vector_id], dtype=np.int64)
                    self._index.add_with_ids(np.ascontiguousarray(row.reshape(1, -1)), ids)
                conn.commit()
            finally:
                conn.close()
            self._save_index()

    def search(self, query_vector, *, candidate_document_ids, limit: int):
        with self._lock:
            if self._index is None or self._dimension is None:
                raise ValueError("Vector index must be ensured before search.")
            query = np.asarray(query_vector, dtype=np.float32)
            if query.shape != (self._dimension,):
                raise ValueError("Query vector dimension mismatch.")
            if limit <= 0:
                return ()
            if not candidate_document_ids:
                return ()

            candidate_set = set(candidate_document_ids)
            query = _normalize_rows(query.reshape(1, -1))
            total = int(self._index.ntotal)
            if total <= 0:
                return ()

            results: list[EvidencePassage] = []
            seen_ids: set[int] = set()
            fetch_k = min(total, max(limit * 4, limit))
            max_k = total

            while fetch_k <= max_k and len(results) < limit:
                scores, ids = self._index.search(np.ascontiguousarray(query), fetch_k)
                rows = self._load_metadata_by_ids(tuple(int(value) for value in ids[0] if value >= 0))
                for rank, (score, vector_id) in enumerate(zip(scores[0], ids[0]), start=1):
                    if vector_id < 0:
                        continue
                    if int(vector_id) in seen_ids:
                        continue
                    meta = rows.get(int(vector_id))
                    if meta is None or meta["document_id"] not in candidate_set:
                        continue
                    seen_ids.add(int(vector_id))
                    results.append(
                        EvidencePassage(
                            citation_id=f"S{len(results) + 1}",
                            passage_id=meta["passage_id"],
                            document_id=meta["document_id"],
                            source_path=meta["source_path"],
                            text=meta["text"],
                            semantic_score=float(score),
                            lexical_rank=rank,
                        )
                    )
                    if len(results) >= limit:
                        break
                if len(results) >= limit or fetch_k >= max_k:
                    break
                fetch_k = min(max_k, fetch_k * 2)

            return tuple(results[:limit])

    def delete_stale(self, *, document_ids: tuple[str, ...], current_text_hashes: dict[str, str]) -> None:
        """Delete stale vectors for candidate documents and rebuild FAISS index."""

        if not document_ids:
            return
        with self._lock:
            if self._index is None:
                return
            conn = self._connect()
            try:
                placeholders = ",".join("?" for _ in document_ids)
                rows = conn.execute(
                    f"SELECT vector_id, passage_id, text_hash FROM vector_metadata WHERE document_id IN ({placeholders})",
                    tuple(document_ids),
                ).fetchall()
                stale_vector_ids = [
                    int(vector_id)
                    for vector_id, passage_id, text_hash in rows
                    if current_text_hashes.get(str(passage_id)) != str(text_hash)
                ]
                if not stale_vector_ids:
                    return
                stale_placeholders = ",".join("?" for _ in stale_vector_ids)
                ids_array = np.asarray(stale_vector_ids, dtype=np.int64)
                self._index.remove_ids(ids_array)
                conn.execute(
                    f"DELETE FROM vector_metadata WHERE vector_id IN ({stale_placeholders})",
                    tuple(stale_vector_ids),
                )
                conn.commit()
            finally:
                conn.close()
            self._save_index()

    def health(self) -> dict[str, object]:
        with self._lock:
            if self._faiss is None:
                return {
                    "status": "unavailable",
                    "engine": "faiss",
                    "index_path": str(self.index_path),
                    "metadata_path": str(self.metadata_db_path),
                    "faiss_available": False,
                    "error": self._faiss_error,
                }
            stored_passages = 0
            if self.metadata_db_path.exists():
                conn = self._connect()
                try:
                    self._ensure_schema()
                    stored_passages = int(conn.execute("SELECT COUNT(1) FROM vector_metadata").fetchone()[0])
                finally:
                    conn.close()
            return {
                "status": "ready",
                "engine": "faiss",
                "index_path": str(self.index_path),
                "metadata_path": str(self.metadata_db_path),
                "embedding_model": self._model_id,
                "vector_dimension": self._dimension,
                "stored_passages": stored_passages,
                "faiss_available": True,
            }

    def _require_faiss(self) -> None:
        if self._faiss is None:
            raise FaissUnavailableError(f"FAISS dependency unavailable: {self._faiss_error}")

    def _ensure_paths(self) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.metadata_db_path)

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vector_metadata (
                    vector_id INTEGER PRIMARY KEY,
                    passage_id TEXT NOT NULL UNIQUE,
                    document_id TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    text TEXT NOT NULL,
                    start_offset INTEGER NOT NULL,
                    end_offset INTEGER NOT NULL,
                    text_hash TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    dimension INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vector_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _load_state(self) -> dict[str, object] | None:
        conn = self._connect()
        try:
            self._ensure_schema()
            rows = dict(conn.execute("SELECT key, value FROM vector_state").fetchall())
            if "dimension" not in rows or "embedding_model" not in rows:
                return None
            return {"dimension": int(rows["dimension"]), "embedding_model": rows["embedding_model"]}
        finally:
            conn.close()

    def _store_state(self, *, dimension: int, model_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("INSERT OR REPLACE INTO vector_state(key, value) VALUES ('dimension', ?)", (str(dimension),))
            conn.execute("INSERT OR REPLACE INTO vector_state(key, value) VALUES ('embedding_model', ?)", (model_id,))
            conn.commit()
        finally:
            conn.close()

    def _reset_storage(self) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM vector_metadata")
            conn.execute("DELETE FROM vector_state")
            conn.commit()
        finally:
            conn.close()
        if self.index_path.exists():
            self.index_path.unlink()

    def _load_or_create_faiss_index(self, dimension: int) -> None:
        if self.index_path.exists():
            self._index = self._faiss.read_index(str(self.index_path))
            return
        base = self._faiss.IndexFlatIP(dimension)
        self._index = self._faiss.IndexIDMap2(base)
        self._save_index()

    def _save_index(self) -> None:
        if self._index is None:
            return
        tmp_path = self.index_path.with_suffix(self.index_path.suffix + ".tmp")
        self._faiss.write_index(self._index, str(tmp_path))
        tmp_path.replace(self.index_path)

    def _vector_id_for_passage(self, passage_id: str) -> int:
        digest = hashlib.blake2b(passage_id.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, byteorder="big", signed=False)
        return value & 0x7FFF_FFFF_FFFF_FFFF

    def _remove_vector_if_exists(self, conn: sqlite3.Connection, passage_id: str, default_id: int) -> None:
        row = conn.execute("SELECT vector_id FROM vector_metadata WHERE passage_id=?", (passage_id,)).fetchone()
        vector_id = int(row[0]) if row is not None else default_id
        if self._index is None:
            return
        ids = np.asarray([vector_id], dtype=np.int64)
        self._index.remove_ids(ids)

    def _upsert_metadata(self, conn: sqlite3.Connection, passage: Passage, vector_id: int) -> None:
        updated_at = datetime.now(UTC).isoformat(timespec="seconds")
        text_hash = hashlib.sha256(passage.text.encode("utf-8")).hexdigest()
        conn.execute(
            """
            INSERT OR REPLACE INTO vector_metadata(
                vector_id, passage_id, document_id, source_path, text,
                start_offset, end_offset, text_hash, embedding_model, dimension, updated_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                vector_id,
                passage.passage_id,
                passage.document_id,
                passage.source_path,
                passage.text,
                passage.start_offset,
                passage.end_offset,
                text_hash,
                self._model_id,
                self._dimension,
                updated_at,
            ),
        )

    def _load_metadata_by_ids(self, vector_ids: tuple[int, ...]) -> dict[int, dict[str, str]]:
        if not vector_ids:
            return {}
        conn = self._connect()
        try:
            placeholders = ",".join("?" for _ in vector_ids)
            rows = conn.execute(
                f"SELECT vector_id, passage_id, document_id, source_path, text FROM vector_metadata WHERE vector_id IN ({placeholders})",
                vector_ids,
            ).fetchall()
            return {
                int(row[0]): {
                    "passage_id": row[1],
                    "document_id": row[2],
                    "source_path": row[3],
                    "text": row[4],
                }
                for row in rows
            }
        finally:
            conn.close()



def _normalize_rows(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe_norms = np.where(norms == 0.0, 1.0, norms)
    return matrix / safe_norms
