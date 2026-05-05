from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return tuple(_json_ready(item) for item in value)
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


@dataclass(frozen=True)
class AddSourceResponse:
    """Response payload for source registration."""

    status: str
    source_id: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, object | None]:
        return _json_ready(asdict(self))  # type: ignore[return-value]


@dataclass(frozen=True)
class IndexSourceResponse:
    """Response payload for indexing operations."""

    status: str
    run_id: str | None = None
    rebuild: bool = False
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object | None]:
        return _json_ready(asdict(self))  # type: ignore[return-value]


@dataclass(frozen=True)
class QueryDocumentsResponse:
    """Response payload for document question answering."""

    status: str
    answer: str = ""
    generation_status: str = "not_configured"
    citations: tuple[str, ...] = ()
    evidence: tuple[dict[str, object], ...] = ()
    lexical_candidate_count: int = 0
    refined_passage_count: int = 0
    model_ids: dict[str, str | None] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    elapsed_ms: int = 0

    def to_dict(self) -> dict[str, object]:
        return _json_ready(asdict(self))  # type: ignore[return-value]


@dataclass(frozen=True)
class GetDocumentResponse:
    """Response payload for one indexed document."""

    status: str
    document: dict[str, object] | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, object | None]:
        return _json_ready(asdict(self))  # type: ignore[return-value]


@dataclass(frozen=True)
class DocumentsStatusResponse:
    """Response payload for slice-level status."""

    status: str
    sources: tuple[dict[str, object], ...] = ()
    index: dict[str, object] | None = None
    health: dict[str, object] | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, object | None]:
        return _json_ready(asdict(self))  # type: ignore[return-value]


@dataclass(frozen=True)
class HealthResponse:
    """Response payload for one component health check."""

    status: str
    component: str
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return _json_ready(asdict(self))  # type: ignore[return-value]
