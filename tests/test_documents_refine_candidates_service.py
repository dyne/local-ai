from __future__ import annotations

from local_ai.slices.documents.domain import DocumentText, Passage, SearchCandidate
from local_ai.slices.documents.refine_candidates.service import RefineCandidatesService


class _TextLoader:
    def load_candidate_text(self, candidate):
        return DocumentText(document_id=candidate.document_id, text="hello world")


class _Splitter:
    def split(self, document, *, source_path):
        return (
            Passage(
                passage_id=f"{document.document_id}-p1",
                document_id=document.document_id,
                source_path=source_path,
                text=document.text,
                start_offset=0,
                end_offset=len(document.text),
            ),
        )


class _Embedding:
    model_id = "qwen3-embed-ov"
    dimension = 2

    def embed_passages(self, passages):
        return ((1.0, 0.0),)

    def embed_query(self, query):
        return (1.0, 0.0)


class _VectorIndex:
    def ensure_index(self, *, dimension, model_id):
        self.dimension = dimension
        self.model_id = model_id

    def upsert_passages(self, passages, vectors):
        self.passages = passages

    def search(self, query_vector, *, candidate_document_ids, limit):
        from local_ai.slices.documents.domain import EvidencePassage

        first = self.passages[0]
        return (
            EvidencePassage(
                citation_id="S1",
                passage_id=first.passage_id,
                document_id=first.document_id,
                source_path=first.source_path,
                text=first.text,
                semantic_score=0.9,
            ),
        )


def test_refine_candidates_happy_path() -> None:
    service = RefineCandidatesService(
        text_loader=_TextLoader(),
        splitter=_Splitter(),
        embedding_model=_Embedding(),
        vector_index=_VectorIndex(),
    )
    candidate = SearchCandidate(
        document_id="doc-1",
        source_path="C:\\doc-1.txt",
        title="Doc",
        snippet="snippet",
        lexical_rank=1,
    )
    result = service.execute(query="hello", candidates=(candidate,), max_passages=3, semantic_mode="required")
    assert len(result.evidence) == 1
