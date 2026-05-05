from __future__ import annotations

import time

from local_ai.shared.domain.log_events import LogEvent, LogLevel
from local_ai.shared.logging.log_bus import InMemoryLogBus


def make_legacy_logger_bridge(
    *,
    log_bus: InMemoryLogBus,
    sink_logger,
    source: str,
):
    """Adapt logger(message, verbose, start) callbacks to structured log events."""

    def _logger(message: str, verbose: bool, start_time: float | None = None) -> None:
        sink_logger(message, verbose, start_time)
        if not verbose:
            return
        context = None
        if start_time is not None:
            context = {"elapsed_seconds": round(time.perf_counter() - start_time, 3)}
        log_bus.publish(
            LogEvent.create(
                level=LogLevel.INFO,
                source=source,
                message=message,
                context=context,
            )
        )

    return _logger
