from __future__ import annotations

from collections.abc import Awaitable, Callable
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from local_ai.slices.app_shell.web import register_app_shell_routes


def build_browser_app(
    *,
    index_html: str,
    static_assets_dir: pathlib.Path | None = None,
    create_session_handler: Callable[[object], Awaitable[object]],
    audio_handler: Callable[[str, WebSocket], Awaitable[None]],
    events_handler: Callable[[str], Awaitable[object]],
    close_session_handler: Callable[[str], Awaitable[object]],
    app_roles_handler: Callable[[], Awaitable[object]] | None = None,
    app_logs_handler: Callable[[Request], Awaitable[object]] | None = None,
    app_log_events_handler: Callable[[], Awaitable[object]] | None = None,
    upload_transcription_handler: Callable[[Request], Awaitable[object]] | None = None,
    register_extra_routes: Callable[[FastAPI], None] | None = None,
    startup_hook: Callable[[], None] | None = None,
    shutdown_hook: Callable[[], None] | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def _lifespan(_app: FastAPI):  # type: ignore[unused-private-member]
        if startup_hook is not None:
            startup_hook()
        try:
            yield
        finally:
            if shutdown_hook is not None:
                shutdown_hook()

    app = FastAPI(title="Browser Mic Transcriber", lifespan=_lifespan)

    if static_assets_dir is not None and static_assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(static_assets_dir)), name="assets")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> str:
        return index_html

    @app.post("/session")
    async def create_session(request: Request) -> object:
        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc
        return await create_session_handler(payload)

    @app.websocket("/audio/{session_id}")
    async def audio(session_id: str, websocket: WebSocket) -> None:
        await audio_handler(session_id, websocket)

    @app.get("/events/{session_id}")
    async def events(session_id: str) -> object:
        return await events_handler(session_id)

    @app.delete("/session/{session_id}")
    async def close_session(session_id: str) -> object:
        return await close_session_handler(session_id)

    if upload_transcription_handler is not None:

        @app.post("/api/voice/transcriptions")
        async def upload_transcription(request: Request) -> object:
            return await upload_transcription_handler(request)

    register_app_shell_routes(
        app,
        app_roles_handler=app_roles_handler,
        app_logs_handler=app_logs_handler,
        app_log_events_handler=app_log_events_handler,
    )
    if register_extra_routes is not None:
        register_extra_routes(app)

    return app
