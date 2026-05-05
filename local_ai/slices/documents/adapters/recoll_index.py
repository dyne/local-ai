from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from local_ai.slices.documents.adapters.process_runner import CommandResult, SubprocessCommandRunner
from local_ai.slices.documents.adapters.recoll_config import write_recoll_config
from local_ai.slices.documents.domain import ArchiveSource, IndexRun, SearchCandidate


class RecollAdapterError(RuntimeError):
    """Raised when Recoll lexical adapter cannot complete an operation."""


class RecollLexicalSearchIndex:
    """Recoll-backed lexical search adapter."""

    def __init__(
        self,
        *,
        recoll_bin_dir: Path,
        recoll_home_dir: Path,
        app_data_dir: Path,
        recoll_data_dir: Path | None = None,
        runner: SubprocessCommandRunner | None = None,
    ) -> None:
        self._recoll_bin_dir = recoll_bin_dir
        self._recoll_home_dir = recoll_home_dir
        self._app_data_dir = app_data_dir
        self._recoll_data_dir = recoll_data_dir
        self._runner = runner or SubprocessCommandRunner()
        self._sources: tuple[ArchiveSource, ...] = ()

    def configure_sources(self, sources: tuple[ArchiveSource, ...]) -> None:
        self._sources = sources
        write_recoll_config(recoll_home_dir=self._recoll_home_dir, sources=sources)

    def index(self, *, rebuild: bool) -> IndexRun:
        if rebuild and self._recoll_home_dir.exists():
            self._safe_remove_recoll_home()
            if self._sources:
                write_recoll_config(recoll_home_dir=self._recoll_home_dir, sources=self._sources)
        started_at = datetime.utcnow()
        result = self._run_recoll_command([str(self._recoll_bin_dir / "recollindex.exe")])
        status = "success" if result.returncode == 0 else "failed"
        finished_at = datetime.utcnow()
        return IndexRun(
            run_id=str(uuid4()),
            started_at=started_at,
            finished_at=finished_at,
            status=status,
            rebuild=rebuild,
            error_message=None if status == "success" else _truncate(result.stderr),
        )

    def search(self, query: str, *, limit: int) -> tuple[SearchCandidate, ...]:
        result = self._run_recoll_command(
            [
                str(self._recoll_bin_dir / "recollq.exe"),
                "-n",
                str(limit),
                "-F",
                "url title abstract",
                query,
            ]
        )
        if result.returncode != 0:
            raise RecollAdapterError(f"Recoll query failed: {_truncate(result.stderr)}")
        return _parse_candidates(result.stdout)

    def health(self) -> dict[str, object]:
        recollindex_path = self._recoll_bin_dir / "recollindex.exe"
        recollq_path = self._recoll_bin_dir / "recollq.exe"
        available = recollindex_path.exists() and recollq_path.exists()
        recoll_data_dir, data_dir_error = self._resolve_recoll_data_dir()
        return {
            "status": "ready" if available and recoll_data_dir else ("missing_binaries" if not available else "missing_data_dir"),
            "recoll_home": str(self._recoll_home_dir),
            "recollindex_path": str(recollindex_path),
            "recollq_path": str(recollq_path),
            "recoll_data_dir": str(recoll_data_dir) if recoll_data_dir else None,
            "error": data_dir_error,
            "source_count": len(self._sources),
        }

    def _run_recoll_command(self, command: list[str]) -> CommandResult:
        recollindex_path = self._recoll_bin_dir / "recollindex.exe"
        recollq_path = self._recoll_bin_dir / "recollq.exe"
        if not recollindex_path.exists() or not recollq_path.exists():
            raise RecollAdapterError("Recoll binaries are missing from configured recoll_bin_dir.")
        recoll_data_dir, error = self._resolve_recoll_data_dir()
        if recoll_data_dir is None:
            raise RecollAdapterError(error or "Recoll data directory is missing.")
        recoll_data_dir = self._ensure_recoll_data_layout(recoll_data_dir)
        return self._runner.run(
            command,
            cwd=self._recoll_home_dir,
            extra_path_entries=(self._recoll_bin_dir,),
            extra_env={"RECOLL_DATADIR": str(recoll_data_dir)},
        )

    def _resolve_recoll_data_dir(self) -> tuple[Path | None, str | None]:
        candidates: list[Path] = []
        if self._recoll_data_dir is not None:
            candidates.append(self._recoll_data_dir)
        env_value = os.getenv("RECOLL_DATADIR")
        env_dir = Path(env_value).expanduser() if env_value else None
        if env_dir is not None:
            candidates.append(env_dir)
        candidates.extend(
            [
                self._recoll_bin_dir / "Share",
                self._recoll_bin_dir / "share",
                Path("C:/Program Files (x86)/Recoll/Share"),
                Path("C:/Program Files/Recoll/Share"),
            ]
        )
        for candidate in candidates:
            sample_backends = candidate / "backends"
            install_backends = candidate / "examples" / "backends"
            if sample_backends.is_file() or install_backends.exists():
                return candidate, None
        return (
            None,
            "Recoll installation data not found. Expected a directory with 'backends' (sampleconf) or 'examples/backends'. Set LOCAL_AI_DOCUMENTS_RECOLL_DATA_DIR or RECOLL_DATADIR.",
        )

    def _ensure_recoll_data_layout(self, recoll_data_dir: Path) -> Path:
        examples_backends = recoll_data_dir / "examples" / "backends"
        if examples_backends.exists():
            return recoll_data_dir
        direct_backends = recoll_data_dir / "backends"
        if not direct_backends.is_file():
            return recoll_data_dir
        examples_backends.parent.mkdir(parents=True, exist_ok=True)
        if not examples_backends.exists():
            shutil.copyfile(direct_backends, examples_backends)
        return recoll_data_dir

    def _safe_remove_recoll_home(self) -> None:
        resolved_home = self._recoll_home_dir.resolve()
        resolved_app_data = self._app_data_dir.resolve()
        if resolved_app_data not in resolved_home.parents and resolved_home != resolved_app_data:
            raise RecollAdapterError("Refusing to remove Recoll home outside app data directory.")
        shutil.rmtree(resolved_home)


def _parse_candidates(stdout: str) -> tuple[SearchCandidate, ...]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    candidates: list[SearchCandidate] = []
    for index, line in enumerate(lines, start=1):
        parts = [part.strip() for part in line.split("\t")]
        if len(parts) < 3:
            continue
        raw_path, title, snippet = parts[0], parts[1], parts[2]
        document_id = hashlib.sha256(raw_path.encode("utf-8")).hexdigest()[:16]
        candidates.append(
            SearchCandidate(
                document_id=document_id,
                source_path=raw_path,
                title=title or None,
                snippet=snippet,
                lexical_rank=index,
            )
        )
    return tuple(candidates)


def _truncate(text: str, *, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit]
