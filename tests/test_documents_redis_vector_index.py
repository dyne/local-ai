from __future__ import annotations

import pytest

from local_ai.slices.documents.adapters.redis_vector_index import RedisVectorSearchIndex
from local_ai.slices.documents.domain import Passage


def _passage(document_id: str, passage_id: str, text: str = "text") -> Passage:
    return Passage(
        passage_id=passage_id,
        document_id=document_id,
        source_path=f"C:\\{document_id}.txt",
        text=text,
        start_offset=0,
        end_offset=max(1, len(text)),
    )


def test_ensure_and_upsert_and_search() -> None:
    index = RedisVectorSearchIndex(redis_url="redis://localhost:6379", index_name="idx")
    index.ensure_index(dimension=3, model_id="embed")
    p1 = _passage("doc-1", "p1")
    p2 = _passage("doc-2", "p2")
    index.upsert_passages((p1, p2), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    results = index.search((1.0, 0.0, 0.0), candidate_document_ids=("doc-1",), limit=2)
    assert len(results) == 1
    assert results[0].document_id == "doc-1"


def test_dimension_mismatch_validation() -> None:
    index = RedisVectorSearchIndex(redis_url="redis://localhost:6379", index_name="idx")
    index.ensure_index(dimension=2, model_id="embed")
    p1 = _passage("doc-1", "p1")
    with pytest.raises(ValueError):
        index.upsert_passages((p1,), ((1.0, 0.0, 0.1),))
