from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from local_ai.slices.documents.domain import (
    ArchiveSource,
    DocumentRef,
    DocumentText,
    EvidencePassage,
    IndexRun,
    Passage,
    SearchCandidate,
)


class DocumentRepository(Protocol):
    """Persistence boundary for documents metadata and runs."""

    def save_source(self, source: ArchiveSource) -> ArchiveSource:
        ...

    def list_sources(self) -> Sequence[ArchiveSource]:
        ...

    def save_index_run(self, run: IndexRun) -> None:
        ...

    def get_document_ref(self, document_id: str) -> DocumentRef | None:
        ...


class LexicalSearchIndex(Protocol):
    """Lexical-first retrieval boundary."""

    def configure_sources(self, sources: Sequence[ArchiveSource]) -> None:
        ...

    def index(self, *, rebuild: bool) -> IndexRun:
        ...

    def search(self, query: str, *, limit: int) -> Sequence[SearchCandidate]:
        ...

    def health(self) -> dict[str, object]:
        ...


class CandidateTextLoader(Protocol):
    """Loads bounded text for lexical candidates."""

    def load_candidate_text(self, candidate: SearchCandidate) -> DocumentText:
        ...


class PassageSplitter(Protocol):
    """Splits one document text into source-traceable passages."""

    def split(self, document: DocumentText, *, source_path: str) -> Sequence[Passage]:
        ...


class EmbeddingModel(Protocol):
    """Embeds query and passage text for semantic ranking."""

    @property
    def model_id(self) -> str:
        ...

    @property
    def dimension(self) -> int:
        ...

    def embed_query(self, query: str) -> Sequence[float]:
        ...

    def embed_passages(self, passages: Sequence[Passage]) -> Sequence[Sequence[float]]:
        ...


class VectorSearchIndex(Protocol):
    """Stores and retrieves passage vectors."""

    def ensure_index(self, *, dimension: int, model_id: str) -> None:
        ...

    def upsert_passages(self, passages: Sequence[Passage], vectors: Sequence[Sequence[float]]) -> None:
        ...

    def search(
        self,
        query_vector: Sequence[float],
        *,
        candidate_document_ids: Sequence[str],
        limit: int,
    ) -> Sequence[EvidencePassage]:
        ...

    def health(self) -> dict[str, object]:
        ...


class TextGenerator(Protocol):
    """Generates a grounded answer from context evidence."""

    @property
    def model_id(self) -> str:
        ...

    def generate(self, *, query: str, context: str) -> str:
        ...
