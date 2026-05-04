from __future__ import annotations

from local_ai.slices.documents.request import GetDocumentsStatusRequest
from local_ai.slices.documents.service import handle_documents_status_request
from local_ai.slices.ocr.request import OcrRequest
from local_ai.slices.ocr.service import handle_ocr_request


def test_documents_slice_placeholder_response() -> None:
    response = handle_documents_status_request(GetDocumentsStatusRequest())
    assert response.status == "planned"


def test_ocr_slice_placeholder_response() -> None:
    response = handle_ocr_request(OcrRequest())
    assert response.status == "planned"

