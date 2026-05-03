from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LocalAiRole:
    """Describes one top-level Local AI role shown by the app shell."""

    id: str
    label: str
    summary: str
    status: str
    route: str
    primary_action: str | None = None


_ROLE_CATALOG: tuple[LocalAiRole, ...] = (
    LocalAiRole(
        id="voice",
        label="Voice",
        summary="Realtime microphone transcription with local Whisper.",
        status="available",
        route="voice",
        primary_action="Start recording",
    ),
    LocalAiRole(
        id="documents",
        label="Documents",
        summary="Document workspace and ingestion flow.",
        status="planned",
        route="documents",
        primary_action=None,
    ),
    LocalAiRole(
        id="ocr",
        label="OCR",
        summary="Image and page text extraction workflows.",
        status="planned",
        route="ocr",
        primary_action=None,
    ),
)


def list_local_ai_roles() -> tuple[LocalAiRole, ...]:
    """Return roles in stable UI order without touching runtime backends."""

    return _ROLE_CATALOG


def role_catalog_response() -> dict[str, list[dict[str, object | None]]]:
    """Build the API response shape consumed by the frontend app shell."""

    return {"roles": [asdict(role) for role in list_local_ai_roles()]}

