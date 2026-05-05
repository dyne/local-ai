from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from local_ai.slices.app_shell.web import register_app_shell_routes


def test_register_app_shell_routes_skips_when_handler_is_none() -> None:
    app = FastAPI()
    register_app_shell_routes(app, app_roles_handler=None)

    client = TestClient(app)
    response = client.get("/api/app/roles")
    assert response.status_code == 404


def test_register_app_shell_routes_exposes_roles_endpoint() -> None:
    async def roles_handler() -> object:
        return {"roles": [{"id": "voice"}]}

    app = FastAPI()
    register_app_shell_routes(app, app_roles_handler=roles_handler)

    client = TestClient(app)
    response = client.get("/api/app/roles")
    assert response.status_code == 200
    assert response.json() == {"roles": [{"id": "voice"}]}


def test_register_app_shell_routes_exposes_logs_endpoints() -> None:
    async def logs_handler(_request: Request) -> object:
        return {"events": []}

    async def events_handler() -> object:
        return {"ok": True}

    app = FastAPI()
    register_app_shell_routes(
        app,
        app_roles_handler=None,
        app_logs_handler=logs_handler,
        app_log_events_handler=events_handler,
    )

    client = TestClient(app)
    logs_response = client.get("/api/app/logs")
    events_response = client.get("/api/app/logs/events")
    assert logs_response.status_code == 200
    assert logs_response.json() == {"events": []}
    assert events_response.status_code == 200
    assert events_response.json() == {"ok": True}

