from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


def _load_model_names(config_path: Path) -> tuple[str, ...]:
    if not config_path.exists():
        return ()
    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    model_config_list = payload.get("model_config_list", [])
    names: list[str] = []
    for item in model_config_list:
        config = item.get("config", {})
        name = config.get("name")
        if isinstance(name, str) and name:
            names.append(name)
    return tuple(names)


@dataclass(frozen=True)
class DocumentsConfig:
    """Local runtime configuration for Documents slice adapters."""

    metadata_db_path: Path
    app_data_dir: Path
    recoll_bin_dir: Path
    recoll_home_dir: Path
    recoll_data_dir: Path | None
    redis_url: str
    redis_index_name: str
    ovms_base_url: str
    ovms_config_path: Path
    ovms_setupvars_path: Path
    embedding_model_name: str
    generation_model_name: str | None
    default_max_documents: int = 20
    default_max_passages: int = 8

    @property
    def configured_model_names(self) -> tuple[str, ...]:
        return _load_model_names(self.ovms_config_path)


def load_documents_config(repo_root: Path | None = None) -> DocumentsConfig:
    """Build DocumentsConfig from defaults and environment overrides."""

    root = repo_root if repo_root is not None else _repo_root()
    local_appdata = Path(os.getenv("LOCALAPPDATA", str(root / ".local-ai")))
    app_root = local_appdata / "LocalAI"
    cache_dir = app_root / "Cache"
    data_dir = app_root / "Data"
    app_data_dir = Path(_env("LOCAL_AI_DOCUMENTS_APP_DATA_DIR", str(data_dir / "documents")))
    ovms_config_path = Path(_env("LOCAL_AI_DOCUMENTS_OVMS_CONFIG_PATH", str(root / "llm" / "models" / "config.json")))
    ovms_setupvars_path = Path(
        _env("LOCAL_AI_DOCUMENTS_OVMS_SETUPVARS_PATH", str(root / "llm" / "ovms" / "setupvars.ps1"))
    )
    generation_model = os.getenv("LOCAL_AI_DOCUMENTS_GENERATION_MODEL")
    return DocumentsConfig(
        metadata_db_path=Path(
            _env("LOCAL_AI_DOCUMENTS_METADATA_DB_PATH", str(data_dir / "documents" / "metadata.sqlite3"))
        ),
        app_data_dir=app_data_dir,
        recoll_bin_dir=Path(_env("LOCAL_AI_DOCUMENTS_RECOLL_BIN_DIR", str(root / "recoll"))),
        recoll_home_dir=Path(
            _env("LOCAL_AI_DOCUMENTS_RECOLL_HOME_DIR", str(cache_dir / "documents" / "recoll"))
        ),
        recoll_data_dir=Path(value).expanduser() if (value := os.getenv("LOCAL_AI_DOCUMENTS_RECOLL_DATA_DIR")) else (root / "recoll" / "sampleconf"),
        redis_url=_env("LOCAL_AI_DOCUMENTS_REDIS_URL", "redis://localhost:6379"),
        redis_index_name=_env("LOCAL_AI_DOCUMENTS_REDIS_INDEX_NAME", "local-ai-documents"),
        ovms_base_url=_env("LOCAL_AI_DOCUMENTS_OVMS_URL", "http://127.0.0.1:8080"),
        ovms_config_path=ovms_config_path,
        ovms_setupvars_path=ovms_setupvars_path,
        embedding_model_name=_env("LOCAL_AI_DOCUMENTS_EMBEDDING_MODEL", "qwen3-embed-ov"),
        generation_model_name=generation_model if generation_model else None,
    )
