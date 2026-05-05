from __future__ import annotations

import asyncio

import pytest

from local_ai.shared.domain.log_events import LogEvent, LogLevel
from local_ai.shared.logging.log_bus import InMemoryLogBus


def _event(index: int, *, level: LogLevel = LogLevel.INFO) -> LogEvent:
    return LogEvent.create(
        event_id=f"evt-{index}",
        timestamp=f"2026-05-05T10:00:0{index}.000Z",
        level=level,
        source="voice.runtime",
        message=f"event-{index}",
    )


def test_recent_keeps_order_and_trims_history() -> None:
    bus = InMemoryLogBus(max_history=3, max_queue=2)
    for index in range(5):
        bus.publish(_event(index))

    assert [item.id for item in bus.recent(limit=10)] == ["evt-2", "evt-3", "evt-4"]


def test_recent_filters_level_source_and_query() -> None:
    bus = InMemoryLogBus(max_history=10, max_queue=2)
    bus.publish(LogEvent.create(level="INFO", source="voice.runtime", message="session started"))
    bus.publish(LogEvent.create(level="ERROR", source="voice.upload", message="upload failed", details=["mime"]))

    filtered = bus.recent(limit=10, level=LogLevel.ERROR, source="voice.upload", query="failed")
    assert len(filtered) == 1
    assert filtered[0].source == "voice.upload"


@pytest.mark.anyio
async def test_subscriber_receives_published_events() -> None:
    bus = InMemoryLogBus(max_history=10, max_queue=2)
    queue = bus.subscribe()

    bus.publish(_event(1))
    received = await asyncio.wait_for(queue.get(), timeout=0.2)

    assert received.id == "evt-1"


@pytest.mark.anyio
async def test_queue_overflow_drops_oldest_event() -> None:
    bus = InMemoryLogBus(max_history=10, max_queue=2)
    queue = bus.subscribe()

    bus.publish(_event(1))
    bus.publish(_event(2))
    bus.publish(_event(3))

    first = await asyncio.wait_for(queue.get(), timeout=0.2)
    second = await asyncio.wait_for(queue.get(), timeout=0.2)
    assert [first.id, second.id] == ["evt-2", "evt-3"]


@pytest.mark.anyio
async def test_unsubscribe_stops_future_delivery() -> None:
    bus = InMemoryLogBus(max_history=10, max_queue=2)
    queue = bus.subscribe()
    bus.unsubscribe(queue)

    bus.publish(_event(1))

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(queue.get(), timeout=0.05)
