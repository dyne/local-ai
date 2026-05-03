from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrResponse:
    """Output boundary placeholder for future OCR endpoints."""

    status: str = "planned"
    message: str = "OCR slice is not implemented yet."

