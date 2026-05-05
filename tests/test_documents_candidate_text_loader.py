from __future__ import annotations

from pathlib import Path

from local_ai.slices.documents.adapters.candidate_text_loader import CandidateTextLoader
from local_ai.slices.documents.domain import SearchCandidate


def _candidate(path: Path) -> SearchCandidate:
    return SearchCandidate(
        document_id="doc-1",
        source_path=str(path),
        title="Doc",
        snippet="Snippet",
        lexical_rank=1,
    )


def test_load_utf8_text(tmp_path: Path) -> None:
    source = tmp_path / "doc.txt"
    source.write_text("hello", encoding="utf-8")
    loader = CandidateTextLoader()
    result = loader.load_candidate_text(_candidate(source))
    assert result.text == "hello"
    assert result.warning is None


def test_load_with_bom(tmp_path: Path) -> None:
    source = tmp_path / "doc.txt"
    source.write_bytes("hello".encode("utf-8-sig"))
    loader = CandidateTextLoader()
    result = loader.load_candidate_text(_candidate(source))
    assert result.text == "hello"


def test_missing_file_warning(tmp_path: Path) -> None:
    source = tmp_path / "missing.txt"
    loader = CandidateTextLoader()
    result = loader.load_candidate_text(_candidate(source))
    assert result.text == ""
    assert result.warning is not None


def test_binary_payload_warning(tmp_path: Path) -> None:
    source = tmp_path / "doc.txt"
    source.write_bytes(b"a\x00b")
    loader = CandidateTextLoader()
    result = loader.load_candidate_text(_candidate(source))
    assert result.text == ""
    assert "Binary-like" in (result.warning or "")


def test_truncates_large_text(tmp_path: Path) -> None:
    source = tmp_path / "doc.txt"
    source.write_text("a" * 50, encoding="utf-8")
    loader = CandidateTextLoader(max_characters=10)
    result = loader.load_candidate_text(_candidate(source))
    assert len(result.text) == 10
    assert "truncated" in (result.warning or "")
