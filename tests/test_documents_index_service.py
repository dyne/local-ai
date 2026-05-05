from __future__ import annotations

from pathlib import Path

from local_ai.slices.documents.domain import ArchiveSource
from local_ai.slices.documents.index_source.service import AddSourceService, IndexDocumentsService, build_index_run
from local_ai.slices.documents.request import AddSourceRequest, IndexSourceRequest


class _FakeRepository:
    def __init__(self) -> None:
        self.sources: list[ArchiveSource] = []
        self.saved_runs = []

    def save_source(self, source: ArchiveSource) -> ArchiveSource:
        self.sources.append(source)
        return source

    def list_sources(self):
        return tuple(self.sources)

    def save_index_run(self, run):
        self.saved_runs.append(run)


class _FakeLexicalIndex:
    def __init__(self, *, status: str = "success") -> None:
        self.status = status
        self.configured_sources = ()

    def configure_sources(self, sources):
        self.configured_sources = tuple(sources)

    def index(self, *, rebuild: bool):
        error = None if self.status == "success" else "index error"
        return build_index_run(status=self.status, rebuild=rebuild, error_message=error)


def test_add_source_rejects_missing_path(tmp_path: Path) -> None:
    repository = _FakeRepository()
    service = AddSourceService(repository=repository, app_data_dir=tmp_path / ".local-ai" / "documents")
    response = service.execute(AddSourceRequest(path=str(tmp_path / "missing")))
    assert response.status == "invalid"


def test_add_source_rejects_app_data_subpath(tmp_path: Path) -> None:
    app_data = (tmp_path / ".local-ai" / "documents").resolve()
    source_path = app_data / "nested"
    source_path.mkdir(parents=True)
    repository = _FakeRepository()
    service = AddSourceService(repository=repository, app_data_dir=app_data)
    response = service.execute(AddSourceRequest(path=str(source_path)))
    assert response.status == "invalid"


def test_add_source_success(tmp_path: Path) -> None:
    source_path = tmp_path / "archive"
    source_path.mkdir()
    repository = _FakeRepository()
    service = AddSourceService(repository=repository, app_data_dir=tmp_path / ".local-ai" / "documents")
    response = service.execute(AddSourceRequest(path=str(source_path)))
    assert response.status == "ok"
    assert response.source_id is not None


def test_index_service_no_sources() -> None:
    repository = _FakeRepository()
    service = IndexDocumentsService(repository=repository, lexical_index=_FakeLexicalIndex())
    response = service.execute(IndexSourceRequest())
    assert response.status == "invalid"


def test_index_service_success(tmp_path: Path) -> None:
    repository = _FakeRepository()
    repository.sources.append(ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve())))
    lexical = _FakeLexicalIndex(status="success")
    service = IndexDocumentsService(repository=repository, lexical_index=lexical)
    response = service.execute(IndexSourceRequest(rebuild=True))
    assert response.status == "success"
    assert response.rebuild is True
    assert len(repository.saved_runs) == 1


def test_index_service_failure_propagates_message(tmp_path: Path) -> None:
    repository = _FakeRepository()
    repository.sources.append(ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve())))
    service = IndexDocumentsService(repository=repository, lexical_index=_FakeLexicalIndex(status="failed"))
    response = service.execute(IndexSourceRequest())
    assert response.status == "failed"
    assert response.message == "index error"
