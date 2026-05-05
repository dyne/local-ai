from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request


def register_app_shell_routes(
    app: FastAPI,
    *,
    app_roles_handler: Callable[[], Awaitable[object]] | None,
    app_logs_handler: Callable[[Request], Awaitable[object]] | None = None,
    app_log_events_handler: Callable[[], Awaitable[object]] | None = None,
) -> None:
    """Register app-level shell routes without coupling to voice session handlers."""

    if app_roles_handler is None:
        if app_logs_handler is None and app_log_events_handler is None:
            return

    if app_roles_handler is not None:
        @app.get("/api/app/roles")
        async def app_roles() -> object:
            return await app_roles_handler()

    if app_logs_handler is not None:
        @app.get("/api/app/logs")
        async def app_logs(request: Request) -> object:
            return await app_logs_handler(request)

    if app_log_events_handler is not None:
        @app.get("/api/app/logs/events")
        async def app_log_events() -> object:
            return await app_log_events_handler()

