from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError

from local_ai.slices.documents.adapters.ovms_client import OvmsClient


def test_list_configured_models_from_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "model_config_list": [
                    {"config": {"name": "qwen3-embed-ov"}},
                    {"config": {"name": "qwen3-llm-ov"}},
                ]
            }
        ),
        encoding="utf-8",
    )
    client = OvmsClient(
        base_url="http://127.0.0.1:8080",
        config_path=config_path,
        setup_command="run ovms",
        http_get_fn=lambda url, timeout: (200, "{}"),
    )
    assert client.list_configured_models_from_file() == ("qwen3-embed-ov", "qwen3-llm-ov")


def test_health_unavailable_includes_setup_command(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"model_config_list": []}), encoding="utf-8")

    def _raise(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise URLError("connection refused")

    client = OvmsClient(
        base_url="http://127.0.0.1:8080",
        config_path=config_path,
        setup_command="run ovms",
        http_get_fn=_raise,
    )
    health = client.health(embedding_model="qwen3-embed-ov", generation_model=None)
    assert health["status"] == "unavailable"
    assert health["setup_command"] == "run ovms"


def test_health_ready_marks_model_flags(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"model_config_list": [{"config": {"name": "qwen3-embed-ov"}}]}),
        encoding="utf-8",
    )
    client = OvmsClient(
        base_url="http://127.0.0.1:8080",
        config_path=config_path,
        setup_command="run ovms",
        http_get_fn=lambda url, timeout: (200, "{}"),
    )
    health = client.health(embedding_model="qwen3-embed-ov", generation_model="qwen3-llm-ov")
    assert health["status"] == "ready"
    assert health["embedding_model_ready"] is True
    assert health["generation_model_ready"] is False
