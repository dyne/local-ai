from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TranscribeUploadedMediaRequest:
    """Request contract for uploaded audio/video transcription."""

    source_name: str
    mime_type: str | None
    payload: bytes
    silence_detect: bool = True
    vad_mode: int = 3

