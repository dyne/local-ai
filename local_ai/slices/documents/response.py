from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentsResponse:
    """Output boundary placeholder for future documents endpoints."""

    status: str = "planned"
    message: str = "Documents slice is not implemented yet."

