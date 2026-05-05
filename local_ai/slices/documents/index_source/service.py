from __future__ import annotations

from datetime import datetime
from pathlib import Path
from uuid import uuid4

from local_ai.slices.documents.domain import ArchiveSource, IndexRun
from local_ai.slices.documents.request import AddSourceRequest, IndexSourceRequest
from local_ai.slices.documents.response import AddSourceResponse, IndexSourceResponse


class AddSourceService:
    """Registers new source roots in repository metadata."""

    def __init__(self, *, repository: object, app_data_dir: Path) -> None:
        self._repository = repository
        self._app_data_dir = app_data_dir.resolve()

    def execute(self, request: AddSourceRequest) -> AddSourceResponse:
        path = Path(request.path).expanduser().resolve()
        if not path.exists():
            return AddSourceResponse(status="invalid", message="Source path does not exist.")
        if self._app_data_dir in path.parents or path == self._app_data_dir:
            return AddSourceResponse(status="invalid", message="Source path cannot be inside .local-ai/documents.")
        source = ArchiveSource(
            source_id=str(uuid4()),
            root_path=str(path),
            label=request.label,
        )
        saved = self._repository.save_source(source)
        return AddSourceResponse(status="ok", source_id=saved.source_id, message="Source added.")


class IndexDocumentsService:
    """Runs lexical indexing for configured archive sources."""

    def __init__(self, *, repository: object, lexical_index: object) -> None:
        self._repository = repository
        self._lexical_index = lexical_index

    def execute(self, request: IndexSourceRequest) -> IndexSourceResponse:
        sources = tuple(self._repository.list_sources())
        if not sources:
            return IndexSourceResponse(status="invalid", rebuild=request.rebuild, message="No enabled sources configured.")
        self._lexical_index.configure_sources(sources)
        run = self._lexical_index.index(rebuild=request.rebuild)
        self._repository.save_index_run(run)
        return IndexSourceResponse(
            status=run.status,
            run_id=run.run_id,
            rebuild=run.rebuild,
            started_at=run.started_at,
            finished_at=run.finished_at,
            message=run.error_message,
        )


def build_index_run(*, status: str, rebuild: bool, error_message: str | None = None) -> IndexRun:
    """Build a run summary value used by tests and fakes."""

    now = datetime.utcnow()
    return IndexRun(
        run_id=str(uuid4()),
        started_at=now,
        finished_at=now,
        status=status,
        rebuild=rebuild,
        error_message=error_message,
    )
