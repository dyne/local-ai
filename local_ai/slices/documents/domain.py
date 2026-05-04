from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path


@dataclass(frozen=True)
class ArchiveSource:
    """Configured archive root that can be indexed by the Documents slice."""

    source_id: str
    root_path: str
    label: str | None = None

    def __post_init__(self) -> None:
        path = Path(self.root_path)
        if not path.is_absolute():
            raise ValueError("Archive source path must be absolute.")


@dataclass(frozen=True)
class DocumentRef:
    """Stable identifier and metadata for one indexed document."""

    document_id: str
    source_id: str
    source_path: str
    title: str | None = None
    mime_type: str | None = None


@dataclass(frozen=True)
class DocumentText:
    """Bounded textual content loaded for candidate refinement."""

    document_id: str
    text: str
    warning: str | None = None


@dataclass(frozen=True)
class Passage:
    """Passage extracted from one document with source offsets."""

    passage_id: str
    document_id: str
    source_path: str
    text: str
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        if self.start_offset < 0 or self.end_offset < 0:
            raise ValueError("Passage offsets must be non-negative.")
        if self.start_offset >= self.end_offset:
            raise ValueError("Passage start_offset must be less than end_offset.")


@dataclass(frozen=True)
class SearchCandidate:
    """First-stage lexical result returned by the search adapter."""

    document_id: str
    source_path: str
    title: str | None
    snippet: str
    lexical_rank: int
    lexical_score: float | None = None


@dataclass(frozen=True)
class EvidencePassage:
    """Ranked evidence passage used for answer assembly."""

    citation_id: str
    passage_id: str
    document_id: str
    source_path: str
    text: str
    semantic_score: float
    lexical_rank: int | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.semantic_score):
            raise ValueError("Evidence semantic_score must be finite.")


@dataclass(frozen=True)
class IndexRun:
    """Summary of one indexing run."""

    run_id: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    rebuild: bool
    error_message: str | None = None


@dataclass(frozen=True)
class VectorIndexStatus:
    """Health and metadata for vector index readiness."""

    status: str
    index_name: str
    embedding_model: str | None = None
    vector_dimension: int | None = None


@dataclass(frozen=True)
class ModelServerStatus:
    """Health summary for the local model runtime."""

    status: str
    base_url: str
    embedding_model_ready: bool
    generation_model_ready: bool
    setup_command: str | None = None


@dataclass(frozen=True)
class DocumentsAnswer:
    """Generated or evidence-only answer returned to callers."""

    answer: str
    generation_status: str
    citations: tuple[str, ...]
    evidence: tuple[EvidencePassage, ...]

    def __post_init__(self) -> None:
        evidence_citations = {item.citation_id for item in self.evidence}
        for citation in self.citations:
            if citation not in evidence_citations:
                raise ValueError("Answer citations must map to returned evidence.")
