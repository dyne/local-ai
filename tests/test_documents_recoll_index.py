from __future__ import annotations

from pathlib import Path

import pytest

from local_ai.slices.documents.adapters.process_runner import CommandResult
from local_ai.slices.documents.adapters.recoll_index import RecollAdapterError, RecollLexicalSearchIndex
from local_ai.slices.documents.domain import ArchiveSource


class _FakeRunner:
    def __init__(self, result: CommandResult) -> None:
        self._result = result
        self.commands: list[list[str]] = []
        self.calls: list[dict[str, object]] = []

    def run(self, command, **kwargs):  # type: ignore[no-untyped-def]
        self.commands.append(list(command))
        self.calls.append(dict(kwargs))
        return self._result


def _prepare_recoll_bin_dir(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "recoll"
    bin_dir.mkdir(parents=True)
    (bin_dir / "recollindex.exe").write_text("", encoding="utf-8")
    (bin_dir / "recollq.exe").write_text("", encoding="utf-8")
    (bin_dir / "Share" / "examples").mkdir(parents=True)
    (bin_dir / "Share" / "examples" / "backends").write_text("", encoding="utf-8")
    return bin_dir


def test_search_parses_candidates(tmp_path: Path) -> None:
    bin_dir = _prepare_recoll_bin_dir(tmp_path)
    runner = _FakeRunner(
        CommandResult(
            returncode=0,
            stdout="C:\\a.txt\tDoc A\tSnippet A\nC:\\b.txt\tDoc B\tSnippet B\n",
            stderr="",
            elapsed_ms=10,
        )
    )
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        runner=runner,  # type: ignore[arg-type]
    )
    results = index.search("query", limit=2)
    assert len(results) == 2
    assert results[0].source_path == "C:\\a.txt"
    assert results[0].lexical_rank == 1


def test_search_raises_on_non_zero_exit(tmp_path: Path) -> None:
    bin_dir = _prepare_recoll_bin_dir(tmp_path)
    runner = _FakeRunner(CommandResult(returncode=1, stdout="", stderr="boom", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        runner=runner,  # type: ignore[arg-type]
    )
    with pytest.raises(RecollAdapterError):
        index.search("query", limit=2)


def test_index_returns_failed_status_on_error(tmp_path: Path) -> None:
    bin_dir = _prepare_recoll_bin_dir(tmp_path)
    runner = _FakeRunner(CommandResult(returncode=1, stdout="", stderr="index failed", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        runner=runner,  # type: ignore[arg-type]
    )
    source = ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve()))
    index.configure_sources((source,))
    run = index.index(rebuild=False)
    assert run.status == "failed"
    assert run.error_message == "index failed"


def test_rebuild_path_safety_rejects_external_path(tmp_path: Path) -> None:
    bin_dir = _prepare_recoll_bin_dir(tmp_path)
    runner = _FakeRunner(CommandResult(returncode=0, stdout="", stderr="", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "outside",
        app_data_dir=tmp_path / "app-data",
        runner=runner,  # type: ignore[arg-type]
    )
    (tmp_path / "outside").mkdir(parents=True)
    with pytest.raises(RecollAdapterError):
        index.index(rebuild=True)


def test_health_reports_binary_paths(tmp_path: Path) -> None:
    bin_dir = _prepare_recoll_bin_dir(tmp_path)
    runner = _FakeRunner(CommandResult(returncode=0, stdout="", stderr="", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        runner=runner,  # type: ignore[arg-type]
    )
    health = index.health()
    assert health["status"] == "ready"
    assert str(bin_dir / "recollindex.exe") == health["recollindex_path"]


def test_health_reports_missing_data_dir(tmp_path: Path) -> None:
    bin_dir = tmp_path / "recoll"
    bin_dir.mkdir(parents=True)
    (bin_dir / "recollindex.exe").write_text("", encoding="utf-8")
    (bin_dir / "recollq.exe").write_text("", encoding="utf-8")
    runner = _FakeRunner(CommandResult(returncode=0, stdout="", stderr="", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        runner=runner,  # type: ignore[arg-type]
    )
    health = index.health()
    assert health["status"] == "missing_data_dir"
    assert "Recoll installation data not found" in str(health["error"])


def test_health_accepts_sampleconf_backends_file(tmp_path: Path) -> None:
    bin_dir = tmp_path / "recoll"
    bin_dir.mkdir(parents=True)
    (bin_dir / "recollindex.exe").write_text("", encoding="utf-8")
    (bin_dir / "recollq.exe").write_text("", encoding="utf-8")
    sampleconf = bin_dir / "sampleconf"
    sampleconf.mkdir(parents=True)
    (sampleconf / "backends").write_text("", encoding="utf-8")
    runner = _FakeRunner(CommandResult(returncode=0, stdout="", stderr="", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        recoll_data_dir=sampleconf,
        runner=runner,  # type: ignore[arg-type]
    )
    health = index.health()
    assert health["status"] == "ready"


def test_index_creates_examples_backends_shim_for_sampleconf(tmp_path: Path) -> None:
    bin_dir = tmp_path / "recoll"
    bin_dir.mkdir(parents=True)
    (bin_dir / "recollindex.exe").write_text("", encoding="utf-8")
    (bin_dir / "recollq.exe").write_text("", encoding="utf-8")
    sampleconf = bin_dir / "sampleconf"
    sampleconf.mkdir(parents=True)
    (sampleconf / "backends").write_text("backend config", encoding="utf-8")
    runner = _FakeRunner(CommandResult(returncode=0, stdout="", stderr="", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        recoll_data_dir=sampleconf,
        runner=runner,  # type: ignore[arg-type]
    )
    source = ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve()))
    index.configure_sources((source,))
    run = index.index(rebuild=False)
    assert run.status == "success"
    assert (sampleconf / "examples" / "backends").exists()


def test_index_sets_recoll_env_vars(tmp_path: Path) -> None:
    bin_dir = _prepare_recoll_bin_dir(tmp_path)
    runner = _FakeRunner(CommandResult(returncode=0, stdout="", stderr="", elapsed_ms=8))
    index = RecollLexicalSearchIndex(
        recoll_bin_dir=bin_dir,
        recoll_home_dir=tmp_path / "home",
        app_data_dir=tmp_path / "app-data",
        runner=runner,  # type: ignore[arg-type]
    )
    source = ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve()))
    index.configure_sources((source,))
    run = index.index(rebuild=False)
    assert run.status == "success"
    assert runner.calls
    extra_env = runner.calls[-1].get("extra_env")
    assert isinstance(extra_env, dict)
    assert extra_env["RECOLL_CONFDIR"] == str((tmp_path / "home"))
