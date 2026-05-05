from __future__ import annotations


def build_documents_prompt(*, query: str, context: str) -> str:
    """Build a grounded prompt for local OVMS generation."""

    return (
        "You are Local AI Documents.\n"
        "Use only the provided sources.\n"
        "Cite supporting sources with IDs like [S1].\n"
        "If evidence is insufficient, say you do not have enough evidence in indexed documents.\n\n"
        f"User query:\n{query}\n\n"
        f"Context:\n{context}\n"
    )
