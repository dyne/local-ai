from __future__ import annotations

from datetime import datetime

import pytest

from local_ai.slices.documents.domain import (
    ArchiveSource,
    DocumentsAnswer,
    EvidencePassage,
    IndexRun,
    Passage,
)


def test_archive_source_requires_absolute_path() -> None:
    with pytest.raises(ValueError):
        ArchiveSource(source_id="src-1", root_path="relative/path")


def test_passage_offsets_are_valid() -> None:
    passage = Passage(
        passage_id="p-1",
        document_id="doc-1",
        source_path="C:\\repo\\doc.txt",
        text="hello world",
        start_offset=0,
        end_offset=5,
    )
    assert passage.end_offset == 5


def test_passage_rejects_invalid_offsets() -> None:
    with pytest.raises(ValueError):
        Passage(
            passage_id="p-1",
            document_id="doc-1",
            source_path="C:\\repo\\doc.txt",
            text="hello world",
            start_offset=10,
            end_offset=10,
        )


def test_evidence_requires_finite_score() -> None:
    with pytest.raises(ValueError):
        EvidencePassage(
            citation_id="S1",
            passage_id="p-1",
            document_id="doc-1",
            source_path="C:\\repo\\doc.txt",
            text="hello",
            semantic_score=float("inf"),
        )


def test_documents_answer_citations_must_match_evidence() -> None:
    evidence = (
        EvidencePassage(
            citation_id="S1",
            passage_id="p-1",
            document_id="doc-1",
            source_path="C:\\repo\\doc.txt",
            text="hello",
            semantic_score=0.9,
        ),
    )
    with pytest.raises(ValueError):
        DocumentsAnswer(
            answer="answer",
            generation_status="not_configured",
            citations=("S2",),
            evidence=evidence,
        )


def test_index_run_shape_is_constructible() -> None:
    run = IndexRun(
        run_id="run-1",
        started_at=datetime.utcnow(),
        finished_at=None,
        status="running",
        rebuild=False,
    )
    assert run.status == "running"
