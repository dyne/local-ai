from __future__ import annotations

from dataclasses import dataclass

from local_ai.slices.documents.adapters.candidate_text_loader import CandidateTextLoader
from local_ai.slices.documents.adapters.ovms_client import OvmsClient
from local_ai.slices.documents.adapters.ovms_embeddings import OvmsEmbeddingModel
from local_ai.slices.documents.adapters.ovms_generator import OvmsTextGenerator
from local_ai.slices.documents.adapters.recoll_index import RecollLexicalSearchIndex
from local_ai.slices.documents.adapters.redis_vector_index import RedisVectorSearchIndex
from local_ai.slices.documents.adapters.sqlite_repository import SqliteDocumentsRepository
from local_ai.slices.documents.config import DocumentsConfig, load_documents_config
from local_ai.slices.documents.index_source.service import AddSourceService, IndexDocumentsService
from local_ai.slices.documents.passage_splitter import DeterministicPassageSplitter
from local_ai.slices.documents.query_archive.service import QueryDocumentsService
from local_ai.slices.documents.refine_candidates.service import RefineCandidatesService
from local_ai.slices.documents.status.service import DocumentsStatusService


@dataclass(frozen=True)
class DocumentsServiceBundle:
    """Container for documents slice services and adapters."""

    config: DocumentsConfig
    repository: SqliteDocumentsRepository
    lexical_index: RecollLexicalSearchIndex
    text_loader: CandidateTextLoader
    ovms_client: OvmsClient
    embedding_model: OvmsEmbeddingModel
    text_generator: OvmsTextGenerator | None
    splitter: DeterministicPassageSplitter
    vector_index: RedisVectorSearchIndex
    refine_candidates_service: RefineCandidatesService
    query_documents_service: QueryDocumentsService
    status_service: DocumentsStatusService
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
        recoll_data_dir=resolved_config.recoll_data_dir,
    )
    text_loader = CandidateTextLoader()
    splitter = DeterministicPassageSplitter()
    vector_index = RedisVectorSearchIndex(
        redis_url=resolved_config.redis_url,
        index_name=resolved_config.redis_index_name,
    )
    setup_command = (
        "cd C:\\Users\\denis\\devel\\local-ai\\llm; "
        ".\\ovms\\setupvars.ps1; "
        "ovms --rest_port 8080 --config_path C:\\Users\\denis\\devel\\local-ai\\llm\\models\\config.json"
    )
    ovms_client = OvmsClient(
        base_url=resolved_config.ovms_base_url,
        config_path=resolved_config.ovms_config_path,
        setup_command=setup_command,
        embedding_model_name=resolved_config.embedding_model_name,
    )
    embedding_model = OvmsEmbeddingModel(
        base_url=resolved_config.ovms_base_url,
        model_name=resolved_config.embedding_model_name,
        setup_command=setup_command,
    )
    text_generator = None
    if resolved_config.generation_model_name:
        text_generator = OvmsTextGenerator(
            base_url=resolved_config.ovms_base_url,
            model_name=resolved_config.generation_model_name,
            setup_command=setup_command,
        )
    status_service = DocumentsStatusService(
        repository=repository,
        lexical_index=lexical_index,
        ovms_client=ovms_client,
    )
    refine_candidates_service = RefineCandidatesService(
        text_loader=text_loader,
        splitter=splitter,
        embedding_model=embedding_model,
        vector_index=vector_index,
    )
    query_documents_service = QueryDocumentsService(
        lexical_index=lexical_index,
        refine_service=refine_candidates_service,
        text_generator=text_generator,
    )
    add_source_service = AddSourceService(repository=repository, app_data_dir=resolved_config.app_data_dir)
    index_documents_service = IndexDocumentsService(repository=repository, lexical_index=lexical_index)
    return DocumentsServiceBundle(
        config=resolved_config,
        repository=repository,
        lexical_index=lexical_index,
        text_loader=text_loader,
        ovms_client=ovms_client,
        embedding_model=embedding_model,
        text_generator=text_generator,
        splitter=splitter,
        vector_index=vector_index,
        refine_candidates_service=refine_candidates_service,
        query_documents_service=query_documents_service,
        status_service=status_service,
        add_source_service=add_source_service,
        index_documents_service=index_documents_service,
    )
