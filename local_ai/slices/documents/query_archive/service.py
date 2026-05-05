from __future__ import annotations

import time

from local_ai.slices.documents.context import assemble_context
from local_ai.slices.documents.prompt_policy import build_documents_prompt
from local_ai.slices.documents.request import QueryDocumentsRequest
from local_ai.slices.documents.response import QueryDocumentsResponse


class QueryDocumentsService:
    """Orchestrates lexical retrieval, refinement, context assembly, and generation."""

    def __init__(self, *, lexical_index: object, refine_service: object, text_generator: object | None = None) -> None:
        self._lexical_index = lexical_index
        self._refine_service = refine_service
        self._text_generator = text_generator

    def execute(self, request: QueryDocumentsRequest) -> QueryDocumentsResponse:
        started = time.perf_counter()
        candidates = tuple(self._lexical_index.search(request.query, limit=request.max_documents))
        if not candidates:
            elapsed = int((time.perf_counter() - started) * 1000)
            return QueryDocumentsResponse(
                status="ok",
                answer="",
                generation_status="no_evidence",
                lexical_candidate_count=0,
                refined_passage_count=0,
                warnings=("No lexical candidates matched the query.",),
                elapsed_ms=elapsed,
            )
        refined = self._refine_service.execute(
            query=request.query,
            candidates=candidates,
            max_passages=request.max_passages,
            semantic_mode=request.semantic_mode,
        )
        context_text, citations = assemble_context(
            evidence=refined.evidence,
            character_budget=request.context_character_budget,
        )
        if self._text_generator is None:
            answer_text = ""
            generation_status = "not_configured"
            model_ids = {"embedding": None, "generation": None}
        else:
            prompt = build_documents_prompt(query=request.query, context=context_text)
            answer_text = self._text_generator.generate(query=request.query, context=prompt)
            generation_status = "generated"
            model_ids = {"embedding": None, "generation": self._text_generator.model_id}
        elapsed = int((time.perf_counter() - started) * 1000)
        evidence_payload = tuple(
            {
                "citation_id": item.citation_id,
                "passage_id": item.passage_id,
                "document_id": item.document_id,
                "source_path": item.source_path,
                "semantic_score": item.semantic_score,
                "text": item.text,
            }
            for item in refined.evidence
        )
        return QueryDocumentsResponse(
            status="ok",
            answer=answer_text,
            generation_status=generation_status,
            citations=citations,
            evidence=evidence_payload,
            lexical_candidate_count=len(candidates),
            refined_passage_count=len(refined.evidence),
            model_ids=model_ids,
            warnings=refined.warnings,
            elapsed_ms=elapsed,
        )
