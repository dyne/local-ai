from __future__ import annotations

from dataclasses import dataclass

from local_ai.slices.documents.domain import EvidencePassage, SearchCandidate


@dataclass(frozen=True)
class RefineCandidatesResult:
    evidence: tuple[EvidencePassage, ...]
    warnings: tuple[str, ...]


class RefineCandidatesService:
    """Candidate-scoped semantic refinement over lexical search results."""

    def __init__(self, *, text_loader: object, splitter: object, embedding_model: object, vector_index: object) -> None:
        self._text_loader = text_loader
        self._splitter = splitter
        self._embedding_model = embedding_model
        self._vector_index = vector_index

    def execute(
        self,
        *,
        query: str,
        candidates: tuple[SearchCandidate, ...],
        max_passages: int,
        semantic_mode: str,
    ) -> RefineCandidatesResult:
        passages = []
        warnings: list[str] = []
        for candidate in candidates:
            text = self._text_loader.load_candidate_text(candidate)
            if text.warning:
                warnings.append(text.warning)
            split = self._splitter.split(text, source_path=candidate.source_path)
            passages.extend(split)
        if not passages:
            return RefineCandidatesResult(evidence=(), warnings=tuple(warnings))
        passage_vectors = tuple(tuple(vector) for vector in self._embedding_model.embed_passages(tuple(passages)))
        self._vector_index.ensure_index(
            dimension=self._embedding_model.dimension,
            model_id=self._embedding_model.model_id,
        )
        self._vector_index.upsert_passages(tuple(passages), passage_vectors)
        query_vector = tuple(self._embedding_model.embed_query(query))
        candidate_document_ids = tuple(candidate.document_id for candidate in candidates)
        evidence = self._vector_index.search(
            query_vector,
            candidate_document_ids=candidate_document_ids,
            limit=max_passages,
        )
        if semantic_mode == "required" and not evidence:
            warnings.append("Semantic refinement returned no passages.")
        return RefineCandidatesResult(evidence=evidence, warnings=tuple(warnings))
