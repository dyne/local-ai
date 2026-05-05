from __future__ import annotations

import shutil
from pathlib import Path

from local_ai.slices.documents.domain import ArchiveSource


_DEFAULT_SKIP_DIRS = (
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".local-ai",
    "models",
    "llm/ovms",
    "whisper-tiny-fp16-ov",
    "whisper-small-fp16-ov",
)
_LOCALAI_MARKER = "# LocalAI overrides"


def write_recoll_config(
    *,
    recoll_home_dir: Path,
    sources: tuple[ArchiveSource, ...],
    template_dir: Path | None = None,
    skip_dirs: tuple[str, ...] = _DEFAULT_SKIP_DIRS,
) -> Path:
    """Create Recoll home config using template defaults plus LocalAI overrides."""

    recoll_home_dir.mkdir(parents=True, exist_ok=True)
    if template_dir is not None and template_dir.exists():
        shutil.copytree(template_dir, recoll_home_dir, dirs_exist_ok=True)

    topdirs_value = " ".join(f'"{Path(source.root_path).as_posix()}"' for source in sources)
    skipped_names = " ".join(skip_dirs)
    template_conf = recoll_home_dir / "recoll.conf"
    if template_dir is None:
        base_text = ""
    else:
        base_text = template_conf.read_text(encoding="utf-8") if template_conf.exists() else ""
    if _LOCALAI_MARKER in base_text:
        base_text = base_text.split(_LOCALAI_MARKER, 1)[0]
    base_text = base_text.rstrip("\n")
    prefix = f"{base_text}\n\n" if base_text else ""
    config_text = prefix + (
        f"{_LOCALAI_MARKER}\n"
        f"topdirs = {topdirs_value}\n"
        "idxabsmlen = 262144\n"
        f"skippedNames = {skipped_names}\n"
    )
    config_path = recoll_home_dir / "recoll.conf"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path
