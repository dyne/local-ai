from __future__ import annotations

from pathlib import Path

import pytest

from local_ai.slices.documents.adapters.faiss_vector_index import FaissUnavailableError, FaissVectorSearchIndex
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


def test_ensure_and_upsert_and_search(tmp_path: Path) -> None:
    index = FaissVectorSearchIndex(
        index_path=tmp_path / "vectors.faiss",
        metadata_db_path=tmp_path / "vectors.sqlite3",
    )
    index.ensure_index(dimension=3, model_id="embed")
    p1 = _passage("doc-1", "p1")
    p2 = _passage("doc-2", "p2")
    index.upsert_passages((p1, p2), ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    results = index.search((1.0, 0.0, 0.0), candidate_document_ids=("doc-1",), limit=2)
    assert len(results) == 1
    assert results[0].document_id == "doc-1"


def test_dimension_mismatch_reset(tmp_path: Path) -> None:
    index = FaissVectorSearchIndex(
        index_path=tmp_path / "vectors.faiss",
        metadata_db_path=tmp_path / "vectors.sqlite3",
    )
    index.ensure_index(dimension=2, model_id="embed")
    index.upsert_passages((_passage("doc-1", "p1"),), ((1.0, 0.0),))

    index.ensure_index(dimension=3, model_id="embed")
    assert index.search((1.0, 0.0, 0.0), candidate_document_ids=("doc-1",), limit=2) == ()


def test_metadata_reopen_and_health(tmp_path: Path) -> None:
    index_path = tmp_path / "vectors.faiss"
    metadata_path = tmp_path / "vectors.sqlite3"
    index = FaissVectorSearchIndex(index_path=index_path, metadata_db_path=metadata_path)
    index.ensure_index(dimension=3, model_id="embed")
    index.upsert_passages((_passage("doc-1", "p1"),), ((1.0, 0.0, 0.0),))

    reopened = FaissVectorSearchIndex(index_path=index_path, metadata_db_path=metadata_path)
    reopened.ensure_index(dimension=3, model_id="embed")
    health = reopened.health()

    assert health["status"] == "ready"
    assert health["engine"] == "faiss"
    assert health["stored_passages"] == 1


def test_missing_dependency_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    index = FaissVectorSearchIndex(
        index_path=tmp_path / "vectors.faiss",
        metadata_db_path=tmp_path / "vectors.sqlite3",
    )
    monkeypatch.setattr(index, "_faiss", None)
    monkeypatch.setattr(index, "_faiss_error", "missing")

    with pytest.raises(FaissUnavailableError):
        index.ensure_index(dimension=3, model_id="embed")
