from __future__ import annotations

from local_ai.slices.documents.domain import DocumentText, EvidencePassage, SearchCandidate
from local_ai.slices.documents.query_archive.service import QueryDocumentsService
from local_ai.slices.documents.request import QueryDocumentsRequest
from local_ai.slices.documents.refine_candidates.service import RefineCandidatesResult


class _Lexical:
    def search(self, query: str, *, limit: int) -> tuple[SearchCandidate, ...]:
        return (
            SearchCandidate(
                document_id="doc-1",
                source_path="C:/archive/id.txt",
                title="id.txt",
                snippet="ABC-123 token",
                lexical_rank=1,
            ),
            SearchCandidate(
                document_id="doc-2",
                source_path="C:/archive/notes.txt",
                title="notes.txt",
                snippet="paraphrase",
                lexical_rank=2,
            ),
            SearchCandidate(
                document_id="doc-3",
                source_path="C:/archive/noise.txt",
                title="noise.txt",
                snippet="irrelevant",
                lexical_rank=3,
            ),
        )[:limit]


class _Refine:
    def execute(
        self,
        *,
        query: str,
        candidates: tuple[SearchCandidate, ...],
        max_passages: int,
        semantic_mode: str,
    ) -> RefineCandidatesResult:
        _ = (query, candidates, semantic_mode)
        return RefineCandidatesResult(
            evidence=(
                EvidencePassage(
                    citation_id="S1",
                    passage_id="p1",
                    document_id="doc-1",
                    source_path="C:/archive/id.txt",
                    text="The identifier is ABC-123.",
                    semantic_score=0.98,
                ),
            )[:max_passages],
            warnings=(),
        )


def test_documents_rag_smoke_no_generator() -> None:
    service = QueryDocumentsService(lexical_index=_Lexical(), refine_service=_Refine(), text_generator=None)
    response = service.execute(QueryDocumentsRequest(query="What is ABC-123?"))
    assert response.status == "ok"
    assert response.lexical_candidate_count == 3
    assert response.refined_passage_count == 1
    assert response.generation_status == "not_configured"
    assert response.citations == ("S1",)
    assert response.evidence[0]["document_id"] == "doc-1"
