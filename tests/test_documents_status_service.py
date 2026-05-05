from __future__ import annotations

from local_ai.slices.documents.domain import ArchiveSource
from local_ai.slices.documents.status.service import DocumentsStatusService


class _Repo:
    def list_sources(self):
        return (
            ArchiveSource(source_id="src-1", root_path="C:\\archive", label="Archive"),
        )


class _Lexical:
    def health(self):
        return {"status": "ready"}


class _Ovms:
    def health(self, *, embedding_model, generation_model):
        return {
            "status": "ready",
            "embedding_model": embedding_model,
            "generation_model": generation_model,
        }


def test_status_service_builds_combined_payload() -> None:
    service = DocumentsStatusService(repository=_Repo(), lexical_index=_Lexical(), ovms_client=_Ovms())
    response = service.execute(embedding_model="qwen3-embed-ov", generation_model=None)
    assert response.status == "ok"
    assert len(response.sources) == 1
    assert response.health is not None
    assert response.health["lexical"]["status"] == "ready"
    assert response.health["ovms"]["status"] == "ready"
