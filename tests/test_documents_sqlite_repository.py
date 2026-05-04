from __future__ import annotations

from datetime import datetime
from pathlib import Path

from local_ai.slices.documents.adapters.sqlite_repository import SqliteDocumentsRepository
from local_ai.slices.documents.domain import ArchiveSource, DocumentRef, IndexRun


def test_schema_created_on_init(tmp_path: Path) -> None:
    repo = SqliteDocumentsRepository(db_path=tmp_path / "metadata.sqlite3")
    assert repo.db_path.exists()


def test_save_and_list_sources(tmp_path: Path) -> None:
    repo = SqliteDocumentsRepository(db_path=tmp_path / "metadata.sqlite3")
    source = ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve()), label="Archive")
    repo.save_source(source)
    sources = repo.list_sources()
    assert len(sources) == 1
    assert sources[0].source_id == "src-1"


def test_disable_source_filters_list(tmp_path: Path) -> None:
    repo = SqliteDocumentsRepository(db_path=tmp_path / "metadata.sqlite3")
    source = ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve()), label=None)
    repo.save_source(source)
    repo.disable_source("src-1")
    assert repo.list_sources() == ()


def test_save_and_get_index_run(tmp_path: Path) -> None:
    repo = SqliteDocumentsRepository(db_path=tmp_path / "metadata.sqlite3")
    run = IndexRun(
        run_id="run-1",
        started_at=datetime.utcnow(),
        finished_at=None,
        status="running",
        rebuild=False,
    )
    repo.save_index_run(run)
    loaded = repo.get_index_run("run-1")
    assert loaded is not None
    assert loaded.status == "running"


def test_upsert_and_get_document_ref(tmp_path: Path) -> None:
    repo = SqliteDocumentsRepository(db_path=tmp_path / "metadata.sqlite3")
    document = DocumentRef(
        document_id="doc-1",
        source_id="src-1",
        source_path="C:\\archive\\doc.txt",
        title="Doc",
        mime_type="text/plain",
    )
    repo.upsert_document_ref(document)
    loaded = repo.get_document_ref("doc-1")
    assert loaded is not None
    assert loaded.document_id == "doc-1"


def test_set_and_get_setting(tmp_path: Path) -> None:
    repo = SqliteDocumentsRepository(db_path=tmp_path / "metadata.sqlite3")
    repo.set_setting("vector_index", {"model": "qwen3-embed-ov"})
    payload = repo.get_setting("vector_index")
    assert payload == {"model": "qwen3-embed-ov"}


def test_repository_can_be_reopened(tmp_path: Path) -> None:
    db_path = tmp_path / "metadata.sqlite3"
    repo1 = SqliteDocumentsRepository(db_path=db_path)
    source = ArchiveSource(source_id="src-1", root_path=str((tmp_path / "archive").resolve()), label=None)
    repo1.save_source(source)
    repo2 = SqliteDocumentsRepository(db_path=db_path)
    assert len(repo2.list_sources()) == 1
