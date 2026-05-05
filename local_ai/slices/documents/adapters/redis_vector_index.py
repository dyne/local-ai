from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from local_ai.slices.documents.domain import EvidencePassage, Passage


class RedisUnavailableError(RuntimeError):
    """Raised when Redis vector search is unavailable."""


@dataclass
class RedisVectorSearchIndex:
    """Redis vector index boundary with an in-memory fallback for tests."""

    redis_url: str
    index_name: str

    def __post_init__(self) -> None:
        self._store: dict[str, tuple[Passage, tuple[float, ...]]] = {}
        self._model_id: str | None = None
        self._dimension: int | None = None

    def ensure_index(self, *, dimension: int, model_id: str) -> None:
        if dimension <= 0:
            raise ValueError("Vector dimension must be positive.")
        if self._dimension is not None and self._dimension != dimension:
            self._store.clear()
        if self._model_id is not None and self._model_id != model_id:
            self._store.clear()
        self._dimension = dimension
        self._model_id = model_id

    def upsert_passages(self, passages: tuple[Passage, ...], vectors: tuple[tuple[float, ...], ...]) -> None:
        if len(passages) != len(vectors):
            raise ValueError("Passage and vector counts must match.")
        if self._dimension is None:
            raise ValueError("Vector index must be ensured before upsert.")
        for passage, vector in zip(passages, vectors):
            if len(vector) != self._dimension:
                raise ValueError("Vector dimension mismatch during upsert.")
            self._store[passage.passage_id] = (passage, tuple(vector))

    def search(
        self,
        query_vector: tuple[float, ...],
        *,
        candidate_document_ids: tuple[str, ...],
        limit: int,
    ) -> tuple[EvidencePassage, ...]:
        if self._dimension is None:
            raise ValueError("Vector index must be ensured before search.")
        if len(query_vector) != self._dimension:
            raise ValueError("Query vector dimension mismatch.")
        candidates = []
        candidate_ids = set(candidate_document_ids)
        for passage, vector in self._store.values():
            if passage.document_id not in candidate_ids:
                continue
            score = _cosine_similarity(query_vector, vector)
            candidates.append(
                EvidencePassage(
                    citation_id=f"S{len(candidates) + 1}",
                    passage_id=passage.passage_id,
                    document_id=passage.document_id,
                    source_path=passage.source_path,
                    text=passage.text,
                    semantic_score=score,
                )
            )
        candidates.sort(key=lambda item: item.semantic_score, reverse=True)
        return tuple(candidates[:limit])

    def health(self) -> dict[str, object]:
        return {
            "status": "ready",
            "redis_url": self.redis_url,
            "index_name": self.index_name,
            "embedding_model": self._model_id,
            "vector_dimension": self._dimension,
            "stored_passages": len(self._store),
        }


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sqrt(sum(a * a for a in left))
    right_norm = sqrt(sum(b * b for b in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)
