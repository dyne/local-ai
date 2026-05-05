from __future__ import annotations

from local_ai.slices.documents.query_archive.service import QueryDocumentsService
from local_ai.slices.documents.request import QueryDocumentsRequest


class _Lexical:
    def __init__(self, candidates):
        self._candidates = candidates

    def search(self, query, *, limit):
        return self._candidates


class _Refine:
    class _Result:
        def __init__(self, evidence, warnings):
            self.evidence = evidence
            self.warnings = warnings

    def __init__(self, evidence=(), warnings=()):
        self._result = self._Result(evidence, warnings)

    def execute(self, **kwargs):
        return self._result


class _Generator:
    model_id = "qwen3-llm-ov"

    def generate(self, *, query, context):
        return "generated answer"


def test_query_service_no_candidates() -> None:
    service = QueryDocumentsService(lexical_index=_Lexical(()), refine_service=_Refine(), text_generator=None)
    response = service.execute(QueryDocumentsRequest(query="hello"))
    assert response.generation_status == "no_evidence"


def test_query_service_not_configured_generation() -> None:
    from local_ai.slices.documents.domain import EvidencePassage, SearchCandidate

    candidates = (
        SearchCandidate(
            document_id="doc-1",
            source_path="C:\\doc.txt",
            title="Doc",
            snippet="snip",
            lexical_rank=1,
        ),
    )
    evidence = (
        EvidencePassage(
            citation_id="S1",
            passage_id="p1",
            document_id="doc-1",
            source_path="C:\\doc.txt",
            text="evidence",
            semantic_score=0.9,
        ),
    )
    service = QueryDocumentsService(lexical_index=_Lexical(candidates), refine_service=_Refine(evidence=evidence), text_generator=None)
    response = service.execute(QueryDocumentsRequest(query="hello"))
    assert response.generation_status == "not_configured"
    assert response.refined_passage_count == 1


def test_query_service_generation_path() -> None:
    from local_ai.slices.documents.domain import EvidencePassage, SearchCandidate

    candidates = (
        SearchCandidate(
            document_id="doc-1",
            source_path="C:\\doc.txt",
            title="Doc",
            snippet="snip",
            lexical_rank=1,
        ),
    )
    evidence = (
        EvidencePassage(
            citation_id="S1",
            passage_id="p1",
            document_id="doc-1",
            source_path="C:\\doc.txt",
            text="evidence",
            semantic_score=0.9,
        ),
    )
    service = QueryDocumentsService(
        lexical_index=_Lexical(candidates),
        refine_service=_Refine(evidence=evidence),
        text_generator=_Generator(),
    )
    response = service.execute(QueryDocumentsRequest(query="hello"))
    assert response.generation_status == "generated"
    assert response.answer == "generated answer"
