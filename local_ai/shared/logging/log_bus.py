from __future__ import annotations

import asyncio
from collections import deque
from threading import Lock

from local_ai.shared.domain.log_events import LogEvent, LogLevel


class InMemoryLogBus:
    """Bounded in-memory log event history with async subscribers."""

    def __init__(self, *, max_history: int = 500, max_queue: int = 200) -> None:
        self._history: deque[LogEvent] = deque(maxlen=max_history)
        self._subscribers: set[asyncio.Queue[LogEvent]] = set()
        self._max_queue = max_queue
        self._lock = Lock()

    def subscribe(self) -> asyncio.Queue[LogEvent]:
        """Register a subscriber queue for live events."""

        queue: asyncio.Queue[LogEvent] = asyncio.Queue(maxsize=self._max_queue)
        with self._lock:
            self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[LogEvent]) -> None:
        """Unregister a subscriber queue."""

        with self._lock:
            self._subscribers.discard(queue)

    def publish(self, event: LogEvent) -> None:
        """Store event in history and fan out to subscribers."""

        with self._lock:
            self._history.append(event)
            subscribers = list(self._subscribers)

        for queue in subscribers:
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # If another producer raced, keep newest by dropping one more.
                try:
                    queue.get_nowait()
                    queue.put_nowait(event)
                except (asyncio.QueueEmpty, asyncio.QueueFull):
                    continue

    def recent(
        self,
        *,
        limit: int = 200,
        level: LogLevel | None = None,
        source: str | None = None,
        query: str | None = None,
    ) -> list[LogEvent]:
        """Return recent events with optional level, source, and query filters."""

        with self._lock:
            items = list(self._history)

        lowered_query = (query or "").strip().lower()
        filtered: list[LogEvent] = []
        for event in items:
            if level is not None and event.level is not level:
                continue
            if source is not None and event.source != source:
                continue
            if lowered_query:
                haystack = f"{event.source} {event.message} {' '.join(event.details or ())} {event.level.value}".lower()
                if lowered_query not in haystack:
                    continue
            filtered.append(event)
        return filtered[-max(1, limit) :]
