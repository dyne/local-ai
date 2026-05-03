from __future__ import annotations

from fastapi import FastAPI
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

