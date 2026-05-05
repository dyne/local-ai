from __future__ import annotations

from local_ai.slices.documents.domain import EvidencePassage


def assemble_context(*, evidence: tuple[EvidencePassage, ...], character_budget: int) -> tuple[str, tuple[str, ...]]:
    """Build a deterministic citation-preserving context block."""

    lines: list[str] = []
    citations: list[str] = []
    used = 0
    for item in evidence:
        block = (
            f"[{item.citation_id}] {item.source_path}\n"
            f"passage_id={item.passage_id} score={item.semantic_score:.4f}\n"
            f"{item.text}\n"
        )
        if used + len(block) > character_budget:
            remaining = max(0, character_budget - used)
            if remaining > 0:
                lines.append(block[:remaining])
            break
        lines.append(block)
        citations.append(item.citation_id)
        used += len(block)
    return ("\n".join(lines), tuple(citations))
