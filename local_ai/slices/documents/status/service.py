from __future__ import annotations

from local_ai.slices.documents.response import DocumentsStatusResponse


class DocumentsStatusService:
    """Builds a consolidated readiness status for Documents dependencies."""

    def __init__(self, *, repository: object, lexical_index: object, ovms_client: object) -> None:
        self._repository = repository
        self._lexical_index = lexical_index
        self._ovms_client = ovms_client

    def execute(self, *, embedding_model: str, generation_model: str | None) -> DocumentsStatusResponse:
        sources = tuple(self._repository.list_sources())
        lexical_health = self._lexical_index.health()
        ovms_health = self._ovms_client.health(
            embedding_model=embedding_model,
            generation_model=generation_model,
        )
        payload_sources = tuple(
            {"source_id": source.source_id, "root_path": source.root_path, "label": source.label}
            for source in sources
        )
        return DocumentsStatusResponse(
            status="ok",
            sources=payload_sources,
            health={"lexical": lexical_health, "ovms": ovms_health},
        )
