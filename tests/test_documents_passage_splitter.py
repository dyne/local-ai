from __future__ import annotations

from local_ai.slices.documents.domain import DocumentText
from local_ai.slices.documents.passage_splitter import DeterministicPassageSplitter


def test_splitter_paragraph_mode() -> None:
    splitter = DeterministicPassageSplitter(target_chars=20, max_chars=30)
    doc = DocumentText(document_id="doc-1", text="first\n\nsecond\n\nthird\n")
    passages = splitter.split(doc, source_path="C:\\doc.txt")
    assert len(passages) >= 2
    assert passages[0].start_offset == 0


def test_splitter_dense_fallback() -> None:
    splitter = DeterministicPassageSplitter(target_chars=10, max_chars=12, overlap_chars=4)
    doc = DocumentText(document_id="doc-1", text="a" * 40)
    passages = splitter.split(doc, source_path="C:\\doc.txt")
    assert len(passages) > 1
    assert passages[1].start_offset < passages[1].end_offset


def test_splitter_empty_text() -> None:
    splitter = DeterministicPassageSplitter()
    doc = DocumentText(document_id="doc-1", text="")
    assert splitter.split(doc, source_path="C:\\doc.txt") == ()
