from __future__ import annotations

from local_ai.slices.documents.prompt_policy import build_documents_prompt


def test_prompt_contains_query_and_context() -> None:
    prompt = build_documents_prompt(query="What happened?", context="[S1] Evidence")
    assert "What happened?" in prompt
    assert "[S1] Evidence" in prompt
    assert "Use only the provided sources" in prompt
