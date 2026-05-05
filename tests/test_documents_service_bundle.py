from __future__ import annotations

from pathlib import Path

from local_ai.slices.documents.config import load_documents_config
from local_ai.slices.documents.service_bundle import build_documents_service_bundle


def test_build_service_bundle(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "llm" / "models").mkdir(parents=True)
    (repo_root / "llm" / "ovms").mkdir(parents=True)
    (repo_root / "llm" / "models" / "config.json").write_text('{"model_config_list":[]}', encoding="utf-8")
    (repo_root / "llm" / "ovms" / "setupvars.ps1").write_text("echo ok", encoding="utf-8")
    (repo_root / "recoll").mkdir(parents=True)
    (repo_root / "recoll" / "recollindex.exe").write_text("", encoding="utf-8")
    (repo_root / "recoll" / "recollq.exe").write_text("", encoding="utf-8")

    config = load_documents_config(repo_root=repo_root)
    bundle = build_documents_service_bundle(config=config)

    assert bundle.config.metadata_db_path == config.metadata_db_path
    assert bundle.repository is not None
    assert bundle.lexical_index is not None
    assert bundle.text_loader is not None
    assert bundle.add_source_service is not None
    assert bundle.index_documents_service is not None
