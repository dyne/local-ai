from __future__ import annotations

from dataclasses import dataclass

from local_ai.slices.documents.adapters.candidate_text_loader import CandidateTextLoader
from local_ai.slices.documents.adapters.recoll_index import RecollLexicalSearchIndex
from local_ai.slices.documents.adapters.sqlite_repository import SqliteDocumentsRepository
from local_ai.slices.documents.config import DocumentsConfig, load_documents_config
from local_ai.slices.documents.index_source.service import AddSourceService, IndexDocumentsService


@dataclass(frozen=True)
class DocumentsServiceBundle:
    """Container for documents slice services and adapters."""

    config: DocumentsConfig
    repository: SqliteDocumentsRepository
    lexical_index: RecollLexicalSearchIndex
    text_loader: CandidateTextLoader
    add_source_service: AddSourceService
    index_documents_service: IndexDocumentsService


def build_documents_service_bundle(config: DocumentsConfig | None = None) -> DocumentsServiceBundle:
    """Build the default documents service graph without side-effectful startup."""

    resolved_config = config or load_documents_config()
    repository = SqliteDocumentsRepository(db_path=resolved_config.metadata_db_path)
    lexical_index = RecollLexicalSearchIndex(
        recoll_bin_dir=resolved_config.recoll_bin_dir,
        recoll_home_dir=resolved_config.recoll_home_dir,
        app_data_dir=resolved_config.app_data_dir,
    )
    text_loader = CandidateTextLoader()
    add_source_service = AddSourceService(repository=repository, app_data_dir=resolved_config.app_data_dir)
    index_documents_service = IndexDocumentsService(repository=repository, lexical_index=lexical_index)
    return DocumentsServiceBundle(
        config=resolved_config,
        repository=repository,
        lexical_index=lexical_index,
        text_loader=text_loader,
        add_source_service=add_source_service,
        index_documents_service=index_documents_service,
    )
