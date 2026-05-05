from __future__ import annotations

from local_ai.slices.documents.context import assemble_context
from local_ai.slices.documents.domain import EvidencePassage


def test_assemble_context_with_budget() -> None:
    evidence = (
        EvidencePassage(
            citation_id="S1",
            passage_id="p1",
            document_id="doc-1",
            source_path="C:\\doc.txt",
            text="hello world",
            semantic_score=0.9,
        ),
    )
    context, citations = assemble_context(evidence=evidence, character_budget=1000)
    assert "[S1]" in context
    assert citations == ("S1",)
