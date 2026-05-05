from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
import uuid


class LogLevel(str, Enum):
    """Supported application log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


def normalize_log_level(value: str | LogLevel) -> LogLevel:
    """Normalize a string or enum value into a LogLevel."""

    if isinstance(value, LogLevel):
        return value
    normalized = str(value).strip().upper()
    return LogLevel(normalized)


@dataclass(frozen=True)
class LogEvent:
    """Serializable application log event used by console and browser consumers."""

    id: str
    timestamp: str
    level: LogLevel
    source: str
    message: str
    details: tuple[str, ...] | None = None
    context: dict[str, str | int | float | bool | None] | None = None
    notification: bool | None = None

    @classmethod
    def create(
        cls,
        *,
        level: str | LogLevel,
        source: str,
        message: str,
        details: list[str] | tuple[str, ...] | None = None,
        context: dict[str, str | int | float | bool | None] | None = None,
        notification: bool | None = None,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> LogEvent:
        """Build a log event with generated id and UTC timestamp defaults."""

        return cls(
            id=event_id or str(uuid.uuid4()),
            timestamp=timestamp or datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            level=normalize_log_level(level),
            source=source,
            message=message,
            details=tuple(details) if details else None,
            context=dict(context) if context else None,
            notification=notification,
        )

    def to_dict(self) -> dict[str, object]:
        """Convert log event to a JSON-serializable dictionary."""

        payload: dict[str, object] = {
            "id": self.id,
            "timestamp": self.timestamp,
            "level": self.level.value,
            "source": self.source,
            "message": self.message,
        }
        if self.details is not None:
            payload["details"] = list(self.details)
        if self.context is not None:
            payload["context"] = self.context
        if self.notification is not None:
            payload["notification"] = self.notification
        return payload
