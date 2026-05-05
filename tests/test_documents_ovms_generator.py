from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from local_ai.slices.documents.adapters.ovms_generator import GenerationUnavailableError, OvmsTextGenerator


def test_generation_success() -> None:
    def _post(url: str, payload: dict[str, object], timeout: int) -> tuple[int, str]:
        return 200, json.dumps({"choices": [{"message": {"content": "Answer [S1]"}}]})

    generator = OvmsTextGenerator(
        base_url="http://127.0.0.1:8080",
        model_name="qwen3-gen-ov",
        setup_command="run ovms",
        http_post_fn=_post,
    )
    assert generator.generate(query="Q", context="C") == "Answer [S1]"


def test_generation_unavailable_raises_setup_hint() -> None:
    def _post(url: str, payload: dict[str, object], timeout: int) -> tuple[int, str]:
        raise URLError("down")

    generator = OvmsTextGenerator(
        base_url="http://127.0.0.1:8080",
        model_name="qwen3-gen-ov",
        setup_command="run ovms",
        http_post_fn=_post,
    )
    with pytest.raises(GenerationUnavailableError, match="run ovms"):
        generator.generate(query="Q", context="C")
