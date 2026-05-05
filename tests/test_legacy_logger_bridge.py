from __future__ import annotations

from local_ai.shared.logging.legacy_bridge import make_legacy_logger_bridge
from local_ai.shared.logging.log_bus import InMemoryLogBus


def test_legacy_bridge_publishes_info_when_verbose() -> None:
    captured = []

    def sink(message, verbose, start_time):
        captured.append((message, verbose, start_time))

    bus = InMemoryLogBus(max_history=10, max_queue=2)
    logger = make_legacy_logger_bridge(log_bus=bus, sink_logger=sink, source="voice.runtime")

    logger("hello", True, None)

    assert captured == [("hello", True, None)]
    events = bus.recent(limit=10)
    assert len(events) == 1
    assert events[0].source == "voice.runtime"
    assert events[0].message == "hello"


def test_legacy_bridge_skips_bus_when_not_verbose() -> None:
    bus = InMemoryLogBus(max_history=10, max_queue=2)
    logger = make_legacy_logger_bridge(log_bus=bus, sink_logger=lambda *_: None, source="voice.runtime")

    logger("quiet", False, None)

    assert bus.recent(limit=10) == []
