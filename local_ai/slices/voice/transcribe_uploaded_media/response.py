from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TranscribeUploadedMediaResponse:
    """Response contract for uploaded audio/video transcription."""

    text: str
    duration_seconds: float
    sample_rate: int
    source_name: str
    details: list[str] = field(default_factory=list)

