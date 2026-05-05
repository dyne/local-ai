from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.testclient import TestClient

from local_ai.slices.documents.response import AddSourceResponse, DocumentsStatusResponse, IndexSourceResponse
from local_ai.slices.documents.web import register_documents_routes


@dataclass(frozen=True)
class _Config:
    embedding_model_name: str = "qwen3-embed-ov"
    generation_model_name: str | None = None
    redis_url: str = "redis://localhost:6379"
    redis_index_name: str = "local-ai-documents"


class _StatusService:
    def execute(self, *, embedding_model: str, generation_model: str | None):
        return DocumentsStatusResponse(
            status="ok",
            sources=(),
            health={"ovms": {"embedding_model": embedding_model, "generation_model": generation_model}},
        )


class _AddSourceService:
    def execute(self, request):
        if "invalid" in request.path:
            return AddSourceResponse(status="invalid", message="bad path")
        return AddSourceResponse(status="ok", source_id="src-1", message="created")


class _IndexService:
    def execute(self, request):
        if request.rebuild:
            return IndexSourceResponse(status="success", rebuild=True)
        return IndexSourceResponse(status="invalid", message="no sources")


class _LexicalIndex:
    def health(self):
        return {"status": "ready"}


class _Ovms:
    def health(self, *, embedding_model: str, generation_model: str | None):
        return {"status": "ready", "embedding_model": embedding_model, "generation_model": generation_model}


@dataclass(frozen=True)
class _Bundle:
    config: _Config
    status_service: _StatusService
    add_source_service: _AddSourceService
    index_documents_service: _IndexService
    lexical_index: _LexicalIndex
    ovms_client: _Ovms


def _client() -> TestClient:
    app = FastAPI()
    bundle = _Bundle(
        config=_Config(),
        status_service=_StatusService(),
        add_source_service=_AddSourceService(),
        index_documents_service=_IndexService(),
        lexical_index=_LexicalIndex(),
        ovms_client=_Ovms(),
    )
    register_documents_routes(app, bundle=bundle)
    return TestClient(app)


def test_documents_status_endpoint() -> None:
    response = _client().get("/api/documents/status")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_add_source_endpoint_success() -> None:
    response = _client().post("/api/documents/sources", json={"path": "C:\\archive"})
    assert response.status_code == 200
    assert response.json()["source_id"] == "src-1"


def test_add_source_endpoint_validation_error() -> None:
    response = _client().post("/api/documents/sources", json={"path": "invalid-path"})
    assert response.status_code == 400


def test_index_endpoint_status_codes() -> None:
    response_invalid = _client().post("/api/documents/index", json={})
    response_success = _client().post("/api/documents/index", json={"rebuild": True})
    assert response_invalid.status_code == 400
    assert response_success.status_code == 200


def test_health_endpoints() -> None:
    client = _client()
    assert client.get("/api/documents/health/recoll").status_code == 200
    assert client.get("/api/documents/health/ovms").status_code == 200
    redis_payload = client.get("/api/documents/health/redis").json()
    assert redis_payload["status"] == "not_configured"
