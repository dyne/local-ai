from __future__ import annotations

from local_ai.slices.ocr.request import OcrRequest
from local_ai.slices.ocr.response import OcrResponse


def handle_ocr_request(request: OcrRequest) -> OcrResponse:
    """Return planned-state response for the OCR slice placeholder."""

    if request.role_id != "ocr":
        return OcrResponse(status="invalid", message="Unsupported role id for OCR slice.")
    return OcrResponse()

