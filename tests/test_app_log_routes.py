from __future__ import annotations

import asyncio
import pathlib

from fastapi.testclient import TestClient

from local_ai.shared.domain.log_events import LogEvent, LogLevel
from local_ai.shared.logging.log_bus import InMemoryLogBus
from local_ai.slices.voice.web_ui.service import AudioStreamService, ServerContext


def _make_context() -> ServerContext:
    return ServerContext(
        pipe=object(),
        generate_kwargs={},
        selected_device="CPU",
        model_dir=pathlib.Path("model"),
        silence_detect_default=True,
        vad_mode_default=3,
        chunk_seconds=1.5,
        overlap_seconds=0.0,
        verbose=False,
        start_time=0.0,
        infer_lock=asyncio.Lock(),
    )


def test_app_logs_route_returns_history_and_applies_filters() -> None:
    bus = InMemoryLogBus(max_history=10, max_queue=2)
    bus.publish(LogEvent.create(level=LogLevel.INFO, source="app", message="ready", event_id="1"))
    bus.publish(LogEvent.create(level=LogLevel.ERROR, source="voice.runtime", message="boom", event_id="2"))

    app = AudioStreamService(_make_context(), "<html></html>", log_bus=bus).build_app()
    client = TestClient(app)

    response = client.get("/api/app/logs?level=ERROR")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["events"]) == 1
    assert payload["events"][0]["id"] == "2"


def test_app_logs_route_clamps_limit_and_handles_invalid_level() -> None:
    bus = InMemoryLogBus(max_history=10, max_queue=2)
    for index in range(3):
        bus.publish(LogEvent.create(level=LogLevel.INFO, source="app", message=f"m{index}", event_id=str(index)))

    app = AudioStreamService(_make_context(), "<html></html>", log_bus=bus).build_app()
    client = TestClient(app)

    limited = client.get("/api/app/logs?limit=1")
    invalid = client.get("/api/app/logs?level=BAD")

    assert limited.status_code == 200
    assert [item["id"] for item in limited.json()["events"]] == ["2"]
    assert invalid.status_code == 400


def test_app_log_events_route_is_registered() -> None:
    app = AudioStreamService(_make_context(), "<html></html>", log_bus=InMemoryLogBus()).build_app()
    routes = {(tuple(sorted(getattr(route, "methods", []) or [])), route.path) for route in app.routes}
    assert (("GET",), "/api/app/logs/events") in routes
