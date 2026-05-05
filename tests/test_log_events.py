from __future__ import annotations

import re

from local_ai.shared.domain.log_events import LogEvent, LogLevel, normalize_log_level


def test_normalize_log_level_supports_case_insensitive_strings() -> None:
    assert normalize_log_level("error") is LogLevel.ERROR
    assert normalize_log_level(" Info ") is LogLevel.INFO


def test_log_event_create_generates_defaults() -> None:
    event = LogEvent.create(level="warning", source="voice.upload", message="Upload retried")

    assert re.match(r"^[0-9a-fA-F-]{36}$", event.id)
    assert event.timestamp.endswith("Z")
    assert event.level is LogLevel.WARNING


def test_log_event_to_dict_is_json_serializable_shape() -> None:
    event = LogEvent.create(
        event_id="evt-1",
        timestamp="2026-05-05T10:00:00.000Z",
        level=LogLevel.ERROR,
        source="voice.runtime",
        message="Transcription failed",
        details=["Model unavailable"],
        context={"session_id": "abc"},
        notification=True,
    )

    assert event.to_dict() == {
        "id": "evt-1",
        "timestamp": "2026-05-05T10:00:00.000Z",
        "level": "ERROR",
        "source": "voice.runtime",
        "message": "Transcription failed",
        "details": ["Model unavailable"],
        "context": {"session_id": "abc"},
        "notification": True,
    }
