from __future__ import annotations

import asyncio
import pathlib
from dataclasses import dataclass
from typing import Any

import av
import numpy as np
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ValidationError

from local_ai.slices.voice.shared.audio_processing import TARGET_SAMPLE_RATE, create_audio_preprocessor
from local_ai.slices.voice.shared.transcript_policy import should_suppress_transcript, transcribe_chunk
from local_ai.slices.voice.transcribe_stream.buffer_decoder import decode_audio_message
from local_ai.slices.voice.transcribe_stream.service import prepare_stream_chunks
from local_ai.slices.voice.web_ui.app_factory import build_browser_app
from local_ai.slices.voice.web_ui.audio_decode import try_decode_bytes
from local_ai.slices.voice.web_ui.capture_store import append_capture_audio
from local_ai.slices.voice.web_ui.chunk_pipeline import process_prepared_chunks
from local_ai.slices.voice.web_ui.event_stream import event_stream
from local_ai.slices.voice.web_ui.inference_runner import run_chunk_inference
from local_ai.slices.voice.web_ui.message_processor import process_audio_message
from local_ai.slices.voice.web_ui.session_cleanup import cleanup_session
from local_ai.slices.voice.web_ui.session_decoder import decode_session_message
from local_ai.slices.voice.web_ui.session_state import DEFAULT_AUDIO_BITRATE, SessionState, create_session_state
from local_ai.slices.voice.web_ui.socket_loop import handle_audio_socket_connection
from local_ai.slices.app_shell.role_catalog import role_catalog_response
from local_ai.slices.documents.service_bundle import build_documents_service_bundle
from local_ai.slices.documents.adapters.ovms_lifecycle import OvmsProcessManager
from local_ai.slices.documents.web import register_documents_routes
from local_ai.slices.voice.transcribe_uploaded_media.request import TranscribeUploadedMediaRequest
from local_ai.slices.voice.transcribe_uploaded_media.service import (
    UploadedMediaError,
    MAX_UPLOAD_BYTES,
    transcribe_uploaded_media,
)

DEFAULT_CHUNK_SECONDS = 1.5
DEFAULT_OVERLAP_SECONDS = 0.0
MAX_ENCODED_BUFFER_BYTES = 4 * 1024 * 1024


def _is_local_client(host: str | None) -> bool:
    return host in {"127.0.0.1", "::1", "localhost"}


async def _read_bounded_body(request: Request, max_upload_bytes: int | None) -> bytes:
    if max_upload_bytes is not None:
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError as exc:
                raise HTTPException(
                    status_code=400,
                    detail={"reason": "Invalid Content-Length.", "details": ["Expected an integer byte size."]},
                ) from exc
            if declared_size > max_upload_bytes:
                max_mb = max_upload_bytes // (1024 * 1024)
                raise HTTPException(
                    status_code=413,
                    detail={"reason": "Upload too large.", "details": [f"Max upload size is {max_mb} MB."]},
                )

    chunks: list[bytes] = []
    total_size = 0
    async for chunk in request.stream():
        if not chunk:
            continue
        total_size += len(chunk)
        if max_upload_bytes is not None and total_size > max_upload_bytes:
            max_mb = max_upload_bytes // (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail={"reason": "Upload too large.", "details": [f"Max upload size is {max_mb} MB."]},
            )
        chunks.append(chunk)
    return b"".join(chunks)


class SessionConfig(BaseModel):
    session_id: str
    save_sample: bool = False
    silence_detect: bool = True
    debug: bool = False
    vad_mode: int = 3
    chunk_seconds: float = DEFAULT_CHUNK_SECONDS
    overlap_seconds: float = DEFAULT_OVERLAP_SECONDS
    mime_type: str | None = None
    audio_bitrate: int = DEFAULT_AUDIO_BITRATE


@dataclass
class ServerContext:
    pipe: object
    generate_kwargs: dict[str, object]
    selected_device: str
    model_dir: pathlib.Path
    silence_detect_default: bool
    vad_mode_default: int
    chunk_seconds: float
    overlap_seconds: float
    verbose: bool
    start_time: float
    infer_lock: asyncio.Lock


class AudioStreamService:
    def __init__(
        self,
        ctx: ServerContext,
        index_html: str,
        static_assets_dir: pathlib.Path | None = None,
        *,
        logger: Any = None,
        likely_reason_details_fn: Any = None,
        to_thread_fn: Any = asyncio.to_thread,
    ) -> None:
        self.ctx = ctx
        self.index_html = index_html
        self.static_assets_dir = static_assets_dir
        self.logger = logger or (lambda message, verbose, start_time: None)
        self.likely_reason_details_fn = likely_reason_details_fn or (lambda exc: ())
        self.to_thread_fn = to_thread_fn
        self.sessions: dict[str, SessionState] = {}

    async def _debug(self, session: SessionState, message: str, limit: int = 12) -> None:
        if not session.debug:
            return
        if session.debug_messages_sent >= limit:
            return
        session.debug_messages_sent += 1
        await session.queue.put(f"[debug] {message}")

    def build_app(self) -> FastAPI:
        documents_bundle = build_documents_service_bundle()
        ovms_manager = OvmsProcessManager(
            base_url=documents_bundle.config.ovms_base_url,
            setupvars_path=documents_bundle.config.ovms_setupvars_path,
            config_path=documents_bundle.config.ovms_config_path,
            autostart=documents_bundle.config.ovms_autostart,
        )

        async def app_roles() -> JSONResponse:
            return JSONResponse(role_catalog_response())

        async def events(session_id: str) -> StreamingResponse:
            session = self.sessions.get(session_id)
            if session is None:
                raise HTTPException(status_code=404, detail="Unknown session")
            return StreamingResponse(self._event_stream(session), media_type="text/event-stream")

        async def close_session(session_id: str) -> JSONResponse:
            session = self.sessions.get(session_id)
            if session is not None:
                await self._cleanup_session(session)
            return JSONResponse({"ok": True})

        async def upload_transcription(request: Request) -> JSONResponse:
            source_name = request.headers.get("x-source-name", "upload")
            content_type = request.headers.get("content-type")
            silence_detect = request.query_params.get("silence_detect", "true").lower() != "false"
            client_host = request.client.host if request.client is not None else None
            max_upload_bytes = None if _is_local_client(client_host) else MAX_UPLOAD_BYTES
            try:
                vad_mode = int(request.query_params.get("vad_mode", "3"))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail={"reason": "Invalid vad_mode.", "details": ["Expected integer 0-3."]}) from exc
            if vad_mode not in (0, 1, 2, 3):
                raise HTTPException(status_code=400, detail={"reason": "Invalid vad_mode.", "details": ["Use one of: 0, 1, 2, 3."]})
            try:
                payload = await _read_bounded_body(request, max_upload_bytes)
                response = await transcribe_uploaded_media(
                    request=TranscribeUploadedMediaRequest(
                        source_name=source_name,
                        mime_type=content_type,
                        payload=payload,
                        silence_detect=silence_detect,
                        vad_mode=vad_mode,
                        max_upload_bytes=max_upload_bytes,
                    ),
                    pipe=self.ctx.pipe,
                    generate_kwargs=self.ctx.generate_kwargs,
                    infer_lock=self.ctx.infer_lock,
                    logger=self.logger,
                    start_time=self.ctx.start_time,
                    verbose=self.ctx.verbose,
                    likely_reason_details_fn=self.likely_reason_details_fn,
                    to_thread_fn=self.to_thread_fn,
                )
            except UploadedMediaError as exc:
                raise HTTPException(status_code=exc.status_code, detail={"reason": exc.reason, "details": exc.details}) from exc

            return JSONResponse(
                {
                    "text": response.text,
                    "duration_seconds": response.duration_seconds,
                    "sample_rate": response.sample_rate,
                    "source_name": response.source_name,
                    "details": response.details,
                }
            )

        return build_browser_app(
            index_html=self.index_html,
            static_assets_dir=self.static_assets_dir,
            create_session_handler=self._create_session,
            audio_handler=self._handle_audio_socket,
            events_handler=events,
            close_session_handler=close_session,
            app_roles_handler=app_roles,
            upload_transcription_handler=upload_transcription,
            register_extra_routes=lambda app: register_documents_routes(app, bundle=documents_bundle),
            startup_hook=ovms_manager.startup,
            shutdown_hook=ovms_manager.shutdown,
        )

    async def _create_session(self, payload: SessionConfig) -> JSONResponse:
        try:
            config = payload if isinstance(payload, SessionConfig) else SessionConfig.model_validate(payload)
        except ValidationError as exc:
            message = exc.errors()[0].get("msg", "Invalid session payload.")
            raise HTTPException(status_code=400, detail=f"Invalid session payload: {message}") from exc

        existing = self.sessions.get(config.session_id)
        if existing is not None:
            await self._cleanup_session(existing)

        try:
            self.sessions[config.session_id] = create_session_state(
                session_id=config.session_id,
                save_sample=config.save_sample,
                silence_detect=config.silence_detect,
                debug=config.debug,
                chunk_seconds=config.chunk_seconds,
                overlap_seconds=config.overlap_seconds,
                mime_type=config.mime_type,
                audio_bitrate=config.audio_bitrate,
                create_preprocessor=lambda enabled, vad_mode: create_audio_preprocessor(enabled, vad_mode=vad_mode),
                vad_mode=config.vad_mode,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        await self._debug(
            self.sessions[config.session_id],
            f"session created mime={config.mime_type or 'unknown'} bitrate={config.audio_bitrate} chunk={config.chunk_seconds:.2f}s overlap={config.overlap_seconds:.2f}s save_sample={config.save_sample}",
        )
        return JSONResponse({"ok": True})

    async def _handle_audio_socket(self, session_id: str, websocket: WebSocket) -> None:
        async def infer_for_chunk(*, chunk: np.ndarray, audio_preprocessor: object | None) -> object:
            return await run_chunk_inference(
                chunk=chunk,
                pipe=self.ctx.pipe,
                generate_kwargs=self.ctx.generate_kwargs,
                audio_preprocessor=audio_preprocessor,
                infer_lock=self.ctx.infer_lock,
                transcribe_fn=transcribe_chunk,
                should_suppress_fn=should_suppress_transcript,
                likely_reason_details_fn=self.likely_reason_details_fn,
                to_thread_fn=self.to_thread_fn,
            )

        async def process_chunks(*, session: SessionState, chunks: list[np.ndarray]) -> None:
            await process_prepared_chunks(
                session=session,
                chunks=chunks,
                target_sample_rate=TARGET_SAMPLE_RATE,
                append_capture_audio_fn=append_capture_audio,
                run_chunk_inference_fn=infer_for_chunk,
                debug_fn=self._debug,
            )

        async def process_message(*, session: SessionState, message: dict[str, object], buffered_audio: np.ndarray) -> object:
            return await process_audio_message(
                session=session,
                message=message,
                buffered_audio=buffered_audio,
                verbose=self.ctx.verbose,
                start_time=self.ctx.start_time,
                logger=self.logger,
                debug_fn=self._debug,
                decode_audio_message_fn=self._decode_audio_message,
                prepare_stream_chunks_fn=prepare_stream_chunks,
                process_prepared_chunks_fn=process_chunks,
                cleanup_session_fn=self._cleanup_session,
            )

        await handle_audio_socket_connection(
            session_id=session_id,
            websocket=websocket,
            sessions=self.sessions,
            cleanup_session_fn=self._cleanup_session,
            debug_fn=self._debug,
            process_message_fn=process_message,
            websocket_disconnect_type=WebSocketDisconnect,
        )

    def _decode_audio_message(self, session: SessionState, message: dict[str, object]) -> tuple[np.ndarray, int] | None:
        return decode_session_message(
            session=session,
            message=message,
            max_encoded_buffer_bytes=MAX_ENCODED_BUFFER_BYTES,
            decode_message=lambda **kwargs: decode_audio_message(
                decode_payload=self._try_decode_bytes,
                **kwargs,
            ),
            invalid_data_error_type=av.error.InvalidDataError,
        )

    def _try_decode_bytes(self, payload: bytes, mime_type: str | None) -> tuple[np.ndarray, int] | None:
        return try_decode_bytes(payload=payload, mime_type=mime_type)

    async def _event_stream(self, session: SessionState) -> object:
        async for item in event_stream(queue=session.queue, ping_timeout=15.0):
            yield item

    async def _cleanup_session(self, session: SessionState) -> None:
        await cleanup_session(session=session, sessions=self.sessions, target_sample_rate=TARGET_SAMPLE_RATE)
