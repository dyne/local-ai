from __future__ import annotations

from pathlib import Path

from local_ai.slices.documents.adapters.recoll_config import write_recoll_config
from local_ai.slices.documents.domain import ArchiveSource


def test_write_recoll_config_with_sources(tmp_path: Path) -> None:
    source_a = ArchiveSource(source_id="src-a", root_path=str((tmp_path / "a").resolve()))
    source_b = ArchiveSource(source_id="src-b", root_path=str((tmp_path / "b").resolve()))
    recoll_home = tmp_path / "recoll"

    config_path = write_recoll_config(recoll_home_dir=recoll_home, sources=(source_a, source_b))

    text = config_path.read_text(encoding="utf-8")
    assert "topdirs =" in text
    assert (tmp_path / "a").resolve().as_posix() in text
    assert (tmp_path / "b").resolve().as_posix() in text
    assert "skippedNames" in text


def test_write_recoll_config_is_deterministic(tmp_path: Path) -> None:
    source = ArchiveSource(source_id="src-a", root_path=str((tmp_path / "a").resolve()))
    recoll_home = tmp_path / "recoll"
    first = write_recoll_config(recoll_home_dir=recoll_home, sources=(source,)).read_text(encoding="utf-8")
    second = write_recoll_config(recoll_home_dir=recoll_home, sources=(source,)).read_text(encoding="utf-8")
    assert first == second
