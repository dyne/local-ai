from __future__ import annotations

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


def write_recoll_config(
    *,
    recoll_home_dir: Path,
    sources: tuple[ArchiveSource, ...],
    skip_dirs: tuple[str, ...] = _DEFAULT_SKIP_DIRS,
) -> Path:
    """Create a minimal recoll.conf for configured sources."""

    recoll_home_dir.mkdir(parents=True, exist_ok=True)
    topdirs_value = " ".join(str(Path(source.root_path)) for source in sources)
    skipped_names = " ".join(skip_dirs)
    config_text = (
        f"topdirs = {topdirs_value}\n"
        "idxabsmlen = 262144\n"
        f"skippedNames = {skipped_names}\n"
    )
    config_path = recoll_home_dir / "recoll.conf"
    config_path.write_text(config_text, encoding="utf-8")
    return config_path
