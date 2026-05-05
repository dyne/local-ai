from __future__ import annotations

import json
from pathlib import Path

from local_ai.slices.documents.config import load_documents_config


def test_config_defaults_resolve_from_repo_root(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "llm" / "models").mkdir(parents=True)
    (repo_root / "llm" / "ovms").mkdir(parents=True)
    config_path = repo_root / "llm" / "models" / "config.json"
    config_path.write_text('{"model_config_list": []}', encoding="utf-8")
    (repo_root / "llm" / "ovms" / "setupvars.ps1").write_text("echo ok", encoding="utf-8")

    local_appdata = tmp_path / "localappdata"
    local_appdata.mkdir(parents=True)
    from os import environ
    environ_backup = environ.get("LOCALAPPDATA")
    environ["LOCALAPPDATA"] = str(local_appdata)
    try:
        config = load_documents_config(repo_root=repo_root)
    finally:
        if environ_backup is None:
            del environ["LOCALAPPDATA"]
        else:
            environ["LOCALAPPDATA"] = environ_backup

    assert config.app_data_dir == local_appdata / "LocalAI" / "Data" / "documents"
    assert config.metadata_db_path == local_appdata / "LocalAI" / "Data" / "documents" / "metadata.sqlite3"
    assert config.recoll_home_dir == local_appdata / "LocalAI" / "Cache" / "documents" / "recoll"
    assert config.recoll_bin_dir == repo_root / "recoll"
    assert config.recoll_data_dir == repo_root / "recoll" / "sampleconf"
    assert config.ovms_base_url == "http://127.0.0.1:8080"


def test_config_reads_model_names_from_ovms_config(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "llm" / "models").mkdir(parents=True)
    (repo_root / "llm" / "ovms").mkdir(parents=True)
    (repo_root / "llm" / "ovms" / "setupvars.ps1").write_text("echo ok", encoding="utf-8")
    payload = {
        "model_config_list": [
            {"config": {"name": "qwen3-embed-ov"}},
            {"config": {"name": "qwen3-llm-ov"}},
        ]
    }
    (repo_root / "llm" / "models" / "config.json").write_text(json.dumps(payload), encoding="utf-8")

    config = load_documents_config(repo_root=repo_root)

    assert config.configured_model_names == ("qwen3-embed-ov", "qwen3-llm-ov")


def test_config_environment_overrides(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "llm" / "models").mkdir(parents=True)
    (repo_root / "llm" / "models" / "config.json").write_text('{"model_config_list":[]}', encoding="utf-8")
    (repo_root / "llm" / "ovms").mkdir(parents=True)
    (repo_root / "llm" / "ovms" / "setupvars.ps1").write_text("echo ok", encoding="utf-8")

    monkeypatch.setenv("LOCAL_AI_DOCUMENTS_REDIS_URL", "redis://localhost:6380")
    monkeypatch.setenv("LOCAL_AI_DOCUMENTS_OVMS_URL", "http://127.0.0.1:9000")
    monkeypatch.setenv("LOCAL_AI_DOCUMENTS_GENERATION_MODEL", "qwen3-llm-ov")

    config = load_documents_config(repo_root=repo_root)
    assert config.redis_url == "redis://localhost:6380"
    assert config.ovms_base_url == "http://127.0.0.1:9000"
    assert config.generation_model_name == "qwen3-llm-ov"
