from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from local_ai.slices.documents.adapters.ovms_embeddings import ModelUnavailableError, OvmsEmbeddingModel
from local_ai.slices.documents.domain import Passage


def test_embed_query_uses_v3_endpoint() -> None:
    calls: list[str] = []

    def _post(url: str, payload: dict[str, object], timeout: int) -> tuple[int, str]:
        calls.append(url)
        return 200, json.dumps({"data": [{"embedding": [3.0, 4.0]}]})

    model = OvmsEmbeddingModel(
        base_url="http://127.0.0.1:8080",
        model_name="qwen3-embed-ov",
        setup_command="run ovms",
        http_post_fn=_post,
    )
    vector = model.embed_query("hello")
    assert calls[0].endswith("/v3/embeddings")
    assert len(vector) == 2
    assert vector[0] == pytest.approx(0.6)
    assert model.dimension == 2


def test_embed_passages_batches() -> None:
    def _post(url: str, payload: dict[str, object], timeout: int) -> tuple[int, str]:
        items = payload["input"]
        return 200, json.dumps({"data": [{"embedding": [1.0, 0.0]} for _ in items]})

    model = OvmsEmbeddingModel(
        base_url="http://127.0.0.1:8080",
        model_name="qwen3-embed-ov",
        setup_command="run ovms",
        batch_size=2,
        http_post_fn=_post,
    )
    passages = tuple(
        Passage(
            passage_id=f"p{i}",
            document_id="d1",
            source_path="C:/a.txt",
            text=f"text-{i}",
            start_offset=0,
            end_offset=5,
        )
        for i in range(3)
    )
    vectors = model.embed_passages(passages)
    assert len(vectors) == 3


def test_embed_unavailable_raises_setup_hint() -> None:
    def _post(url: str, payload: dict[str, object], timeout: int) -> tuple[int, str]:
        raise URLError("connection refused")

    model = OvmsEmbeddingModel(
        base_url="http://127.0.0.1:8080",
        model_name="qwen3-embed-ov",
        setup_command="run ovms",
        http_post_fn=_post,
    )
    with pytest.raises(ModelUnavailableError, match="run ovms"):
        model.embed_query("x")
