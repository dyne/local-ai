from __future__ import annotations

from dataclasses import dataclass


_VALID_SEMANTIC_MODES = {"required", "best_effort"}


@dataclass(frozen=True)
class AddSourceRequest:
    """Request payload for adding one archive source root."""

    path: str
    label: str | None = None
    include_globs: tuple[str, ...] = ()
    exclude_globs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("Source path must be non-empty.")


@dataclass(frozen=True)
class IndexSourceRequest:
    """Request payload for indexing configured sources."""

    rebuild: bool = False


@dataclass(frozen=True)
class QueryDocumentsRequest:
    """Request payload for querying indexed documents."""

    query: str
    max_documents: int = 20
    max_passages: int = 8
    context_character_budget: int = 12000
    answer_style: str = "concise"
    require_citations: bool = True
    semantic_mode: str = "required"

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("Query text must be non-empty.")
        if self.max_documents <= 0:
            raise ValueError("max_documents must be positive.")
        if self.max_passages <= 0:
            raise ValueError("max_passages must be positive.")
        if self.context_character_budget <= 0:
            raise ValueError("context_character_budget must be positive.")
        if self.semantic_mode not in _VALID_SEMANTIC_MODES:
            raise ValueError("semantic_mode must be one of: required, best_effort.")


@dataclass(frozen=True)
class GetDocumentRequest:
    """Request payload for loading one document by id."""

    document_id: str

    def __post_init__(self) -> None:
        if not self.document_id.strip():
            raise ValueError("document_id must be non-empty.")


@dataclass(frozen=True)
class GetDocumentsStatusRequest:
    """Request payload for documents slice status."""

    include_health: bool = True


@dataclass(frozen=True)
class HealthRequest:
    """Request payload for one health probe."""

    component: str

    def __post_init__(self) -> None:
        if not self.component.strip():
            raise ValueError("component must be non-empty.")
