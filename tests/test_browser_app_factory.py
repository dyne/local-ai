from __future__ import annotations

import pathlib

from fastapi.testclient import TestClient

from local_ai.slices.voice.web_ui.app_factory import build_browser_app


def test_build_browser_app_registers_expected_routes() -> None:
    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
    )

    routes = {(tuple(sorted(getattr(route, "methods", []) or [])), route.path) for route in app.routes}

    assert (("GET",), "/") in routes
    assert (("POST",), "/session") in routes
    assert (("GET",), "/events/{session_id}") in routes
    assert (("DELETE",), "/session/{session_id}") in routes
    assert ((), "/audio/{session_id}") in routes
    assert (("GET",), "/api/app/roles") not in routes
    assert (("POST",), "/api/voice/transcriptions") not in routes


def test_build_browser_app_registers_app_roles_route_when_handler_provided() -> None:
    async def app_roles_handler() -> object:
        return {"roles": [{"id": "voice"}]}

    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
        app_roles_handler=app_roles_handler,
    )

    client = TestClient(app)
    response = client.get("/api/app/roles")

    assert response.status_code == 200
    assert response.json() == {"roles": [{"id": "voice"}]}


def test_build_browser_app_registers_app_log_routes_when_handlers_provided() -> None:
    async def app_logs_handler(request) -> object:
        return {"query": request.query_params.get("q"), "events": []}

    async def app_log_events_handler() -> object:
        return {"ok": True}

    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
        app_logs_handler=app_logs_handler,
        app_log_events_handler=app_log_events_handler,
    )

    client = TestClient(app)
    logs_response = client.get("/api/app/logs?q=boom")
    events_response = client.get("/api/app/logs/events")

    assert logs_response.status_code == 200
    assert logs_response.json() == {"query": "boom", "events": []}
    assert events_response.status_code == 200
    assert events_response.json() == {"ok": True}


def test_build_browser_app_registers_upload_route_when_handler_provided() -> None:
    async def upload_handler(request) -> object:
        assert request.headers.get("x-source-name") == "sample.wav"
        return {"text": "hello", "duration_seconds": 1.0, "sample_rate": 16000, "source_name": "sample.wav"}

    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
        upload_transcription_handler=upload_handler,
    )
    client = TestClient(app)
    response = client.post(
        "/api/voice/transcriptions",
        content=b"stub",
        headers={"x-source-name": "sample.wav", "content-type": "audio/wav"},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "hello"


def test_build_browser_app_upload_route_passes_empty_body_to_handler() -> None:
    async def upload_handler(request) -> object:
        assert await request.body() == b""
        return {"ok": True}

    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
        upload_transcription_handler=upload_handler,
    )
    client = TestClient(app)
    response = client.post("/api/voice/transcriptions")

    assert response.status_code == 200


def test_build_browser_app_serves_static_assets_when_directory_exists(tmp_path: pathlib.Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "app.js").write_text("console.log('ready');", encoding="utf-8")

    app = build_browser_app(
        index_html="<html><body>ok</body></html>",
        static_assets_dir=assets_dir,
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
    )

    client = TestClient(app)
    response = client.get("/assets/app.js")

    assert response.status_code == 200
    assert "console.log('ready');" in response.text


def test_build_browser_app_passes_json_payload_to_session_handler() -> None:
    received: list[object] = []

    async def create_session_handler(payload: object) -> object:
        received.append(payload)
        return {"ok": True}

    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=create_session_handler,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
    )

    client = TestClient(app)
    response = client.post("/session", json={"session_id": "abc", "chunk_seconds": 1.5})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert received == [{"session_id": "abc", "chunk_seconds": 1.5}]


def test_build_browser_app_returns_400_for_invalid_json_body() -> None:
    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
    )

    client = TestClient(app)
    response = client.post(
        "/session",
        content="{",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid JSON body."}


def test_build_browser_app_registers_extra_routes_callback() -> None:
    called = {"value": False}

    def register_extra(app) -> None:
        called["value"] = True

        @app.get("/extra")
        async def _extra() -> object:
            return {"ok": True}

    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
        register_extra_routes=register_extra,
    )

    client = TestClient(app)
    response = client.get("/extra")

    assert called["value"] is True
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_build_browser_app_runs_startup_and_shutdown_hooks() -> None:
    state = {"started": 0, "stopped": 0}

    def on_startup() -> None:
        state["started"] += 1

    def on_shutdown() -> None:
        state["stopped"] += 1

    app = build_browser_app(
        index_html="<html></html>",
        create_session_handler=lambda payload: None,
        audio_handler=lambda session_id, websocket: None,
        events_handler=lambda session_id: None,
        close_session_handler=lambda session_id: None,
        startup_hook=on_startup,
        shutdown_hook=on_shutdown,
    )

    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200

    assert state["started"] == 1
    assert state["stopped"] == 1
