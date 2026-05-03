from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI


def register_app_shell_routes(app: FastAPI, *, app_roles_handler: Callable[[], Awaitable[object]] | None) -> None:
    """Register app-level shell routes without coupling to voice session handlers."""

    if app_roles_handler is None:
        return

    @app.get("/api/app/roles")
    async def app_roles() -> object:
        return await app_roles_handler()

