from __future__ import annotations

import asyncio
import pathlib

from fastapi.testclient import TestClient

from local_ai.slices.voice.web_ui.service import AudioStreamService, ServerContext


def _context() -> ServerContext:
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


def test_local_file_transcription_route_rejects_non_local_client(monkeypatch) -> None:
    service = AudioStreamService(_context(), "<html></html>")
    app = service.build_app()
    client = TestClient(app)

    response = client.post("/api/voice/transcriptions/local-file", json={"path": "C:\\sample.wav"})

    assert response.status_code == 403


def test_local_file_transcription_route_accepts_local_client(monkeypatch) -> None:
    async def _fake_transcribe(**kwargs):
        return type("Response", (), {
            "text": "ok",
            "duration_seconds": 1.0,
            "sample_rate": 16000,
            "source_name": "sample.wav",
            "details": (),
        })()

    monkeypatch.setattr("local_ai.slices.voice.web_ui.service._is_local_client", lambda host: True)
    monkeypatch.setattr("local_ai.slices.voice.web_ui.service.transcribe_local_media_path", _fake_transcribe)

    service = AudioStreamService(_context(), "<html></html>")
    app = service.build_app()
    client = TestClient(app)

    response = client.post(
        "/api/voice/transcriptions/local-file",
        json={"path": "C:\\sample.wav", "silence_detect": True, "vad_mode": 3},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "ok"
