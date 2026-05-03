from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentsRequest:
    """Input boundary placeholder for future documents endpoints."""

    role_id: str = "documents"

