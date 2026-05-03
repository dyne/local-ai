from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OcrRequest:
    """Input boundary placeholder for future OCR endpoints."""

    role_id: str = "ocr"

