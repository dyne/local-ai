from __future__ import annotations

from local_ai.slices.documents import ports


def test_ports_module_exposes_protocols() -> None:
    assert hasattr(ports, "DocumentRepository")
    assert hasattr(ports, "LexicalSearchIndex")
    assert hasattr(ports, "CandidateTextLoader")
    assert hasattr(ports, "PassageSplitter")
    assert hasattr(ports, "EmbeddingModel")
    assert hasattr(ports, "VectorSearchIndex")
    assert hasattr(ports, "TextGenerator")
