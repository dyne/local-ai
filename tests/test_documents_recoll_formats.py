from __future__ import annotations

import os
from pathlib import Path

import pytest

from local_ai.slices.documents.adapters.candidate_text_loader import CandidateTextLoader
from local_ai.slices.documents.domain import SearchCandidate


@pytest.mark.parametrize(
    ("filename", "content"),
    (
        ("note.txt", "plain text document"),
        ("note.md", "# Heading\nMarkdown body"),
        ("code.py", "def run():\n    return 1\n"),
        ("data.json", '{"key":"value"}'),
    ),
)
def test_text_like_formats_are_loaded(tmp_path: Path, filename: str, content: str) -> None:
    file_path = tmp_path / filename
    file_path.write_text(content, encoding="utf-8")
    loader = CandidateTextLoader()
    candidate = SearchCandidate(
        document_id="doc-1",
        source_path=str(file_path),
        title=filename,
        snippet="",
        lexical_rank=1,
    )
    loaded = loader.load_candidate_text(candidate)
    assert loaded.text
    assert loaded.warning is None


def test_binary_format_returns_warning(tmp_path: Path) -> None:
    file_path = tmp_path / "blob.bin"
    file_path.write_bytes(b"\x00\x01\x02")
    loader = CandidateTextLoader()
    candidate = SearchCandidate(
        document_id="doc-2",
        source_path=str(file_path),
        title="blob.bin",
        snippet="",
        lexical_rank=1,
    )
    loaded = loader.load_candidate_text(candidate)
    assert loaded.text == ""
    assert loaded.warning is not None


@pytest.mark.skipif(
    os.getenv("LOCAL_AI_RECOLL_INTEGRATION") != "1",
    reason="Enable LOCAL_AI_RECOLL_INTEGRATION=1 for real Recoll format checks.",
)
def test_recoll_integration_placeholder() -> None:
    """Optional integration slot for local Recoll format indexing checks."""

