from __future__ import annotations

from local_ai.slices.documents.request import DocumentsRequest
from local_ai.slices.documents.response import DocumentsResponse


def handle_documents_request(request: DocumentsRequest) -> DocumentsResponse:
    """Return planned-state response for the documents slice placeholder."""

    if request.role_id != "documents":
        return DocumentsResponse(status="invalid", message="Unsupported role id for documents slice.")
    return DocumentsResponse()

