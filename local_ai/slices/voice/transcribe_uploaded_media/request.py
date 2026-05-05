from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True)
class TranscribeUploadedMediaRequest:
    """Request contract for uploaded audio/video transcription."""

    source_name: str
    mime_type: str | None
    payload: bytes
    silence_detect: bool = True
    vad_mode: int = 3
    max_upload_bytes: int | None = DEFAULT_MAX_UPLOAD_BYTES


@dataclass(frozen=True)
class TranscribeLocalMediaRequest:
    """Request contract for trusted local-file path transcription."""

    source_path: Path
    silence_detect: bool = True
    vad_mode: int = 3

