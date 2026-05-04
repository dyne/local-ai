from __future__ import annotations

from local_ai.slices.documents.request import GetDocumentsStatusRequest
from local_ai.slices.documents.response import DocumentsStatusResponse


def handle_documents_status_request(request: GetDocumentsStatusRequest) -> DocumentsStatusResponse:
    """Return placeholder status until documents services are fully implemented."""

    _ = request
    return DocumentsStatusResponse(
        status="planned",
        message="Documents slice is not implemented yet.",
    )
