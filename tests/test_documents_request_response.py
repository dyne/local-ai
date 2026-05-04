from __future__ import annotations

import pytest

from local_ai.slices.documents.request import (
    AddSourceRequest,
    GetDocumentRequest,
    HealthRequest,
    QueryDocumentsRequest,
)
from local_ai.slices.documents.response import QueryDocumentsResponse


def test_query_request_defaults() -> None:
    request = QueryDocumentsRequest(query="what is indexed")
    assert request.max_documents == 20
    assert request.max_passages == 8
    assert request.semantic_mode == "required"


def test_query_request_rejects_empty_query() -> None:
    with pytest.raises(ValueError):
        QueryDocumentsRequest(query="   ")


def test_query_request_rejects_invalid_limits() -> None:
    with pytest.raises(ValueError):
        QueryDocumentsRequest(query="x", max_documents=0)
    with pytest.raises(ValueError):
        QueryDocumentsRequest(query="x", max_passages=0)
    with pytest.raises(ValueError):
        QueryDocumentsRequest(query="x", context_character_budget=0)


def test_query_request_rejects_invalid_semantic_mode() -> None:
    with pytest.raises(ValueError):
        QueryDocumentsRequest(query="x", semantic_mode="invalid")


def test_add_source_requires_non_empty_path() -> None:
    with pytest.raises(ValueError):
        AddSourceRequest(path=" ")


def test_get_document_requires_non_empty_id() -> None:
    with pytest.raises(ValueError):
        GetDocumentRequest(document_id=" ")


def test_health_request_requires_component() -> None:
    with pytest.raises(ValueError):
        HealthRequest(component="")


def test_query_response_serialization_shape() -> None:
    response = QueryDocumentsResponse(status="ok", answer="answer", elapsed_ms=12)
    payload = response.to_dict()
    assert payload["status"] == "ok"
    assert payload["answer"] == "answer"
    assert payload["elapsed_ms"] == 12
