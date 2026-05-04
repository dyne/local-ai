from __future__ import annotations

import asyncio

import numpy as np
import pytest

from local_ai.slices.voice.transcribe_uploaded_media.request import TranscribeUploadedMediaRequest
from local_ai.slices.voice.transcribe_uploaded_media.service import (
    UploadedMediaError,
    transcribe_uploaded_media,
)


def test_transcribe_uploaded_media_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_uploaded_media.service.decode_media_file",
        lambda path: (np.array([0.1, 0.2, 0.3], dtype=np.float32), 16000),
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_uploaded_media.service.create_audio_preprocessor",
        lambda enabled, vad_mode=3: None,
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_uploaded_media.service.preprocess_audio",
        lambda audio, sample_rate, preprocessor, verbose, start, logger: audio,
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_uploaded_media.service.ensure_sample_rate",
        lambda audio, sample_rate, verbose, start, logger: (audio, sample_rate),
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_uploaded_media.service.transcribe_chunk",
        lambda pipe, audio, kwargs: "hello world",
    )

    response = asyncio.run(
        transcribe_uploaded_media(
            request=TranscribeUploadedMediaRequest(source_name="clip.wav", mime_type="audio/wav", payload=b"abc"),
            pipe=object(),
            generate_kwargs={},
            infer_lock=asyncio.Lock(),
            logger=lambda *args: None,
            start_time=0.0,
            verbose=False,
            likely_reason_details_fn=lambda exc: ["detail"],
            to_thread_fn=asyncio.to_thread,
        )
    )

    assert response.text == "hello world"
    assert response.sample_rate == 16000
    assert response.source_name == "clip.wav"


def test_transcribe_uploaded_media_raises_for_missing_audio(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise_no_audio(path):
        raise ValueError("No decodable audio stream found")

    monkeypatch.setattr("local_ai.slices.voice.transcribe_uploaded_media.service.decode_media_file", _raise_no_audio)
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_uploaded_media.service.create_audio_preprocessor",
        lambda enabled, vad_mode=3: None,
    )

    with pytest.raises(UploadedMediaError, match="No decodable audio stream found"):
        asyncio.run(
            transcribe_uploaded_media(
                request=TranscribeUploadedMediaRequest(source_name="clip.mp4", mime_type="video/mp4", payload=b"abc"),
                pipe=object(),
                generate_kwargs={},
                infer_lock=asyncio.Lock(),
                logger=lambda *args: None,
                start_time=0.0,
                verbose=False,
                likely_reason_details_fn=lambda exc: ["detail"],
                to_thread_fn=asyncio.to_thread,
            )
        )


def test_transcribe_uploaded_media_rejects_empty_payload() -> None:
    with pytest.raises(UploadedMediaError, match="Upload is empty"):
        asyncio.run(
            transcribe_uploaded_media(
                request=TranscribeUploadedMediaRequest(source_name="empty.wav", mime_type="audio/wav", payload=b""),
                pipe=object(),
                generate_kwargs={},
                infer_lock=asyncio.Lock(),
                logger=lambda *args: None,
                start_time=0.0,
                verbose=False,
                likely_reason_details_fn=lambda exc: ["detail"],
                to_thread_fn=asyncio.to_thread,
            )
        )


def test_transcribe_uploaded_media_rejects_payload_above_configured_limit() -> None:
    with pytest.raises(UploadedMediaError, match="Upload too large") as exc_info:
        asyncio.run(
            transcribe_uploaded_media(
                request=TranscribeUploadedMediaRequest(
                    source_name="large.wav",
                    mime_type="audio/wav",
                    payload=b"abcdef",
                    max_upload_bytes=5,
                ),
                pipe=object(),
                generate_kwargs={},
                infer_lock=asyncio.Lock(),
                logger=lambda *args: None,
                start_time=0.0,
                verbose=False,
                likely_reason_details_fn=lambda exc: ["detail"],
                to_thread_fn=asyncio.to_thread,
            )
        )

    assert exc_info.value.status_code == 413


def test_transcribe_uploaded_media_rejects_invalid_vad_mode() -> None:
    def _raise_invalid_vad(enabled, vad_mode=3):
        raise RuntimeError("Invalid VAD mode: 8. Use 0, 1, 2, or 3.")

    with pytest.raises(UploadedMediaError, match="Invalid vad_mode") as exc_info:
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(
                "local_ai.slices.voice.transcribe_uploaded_media.service.decode_media_file",
                lambda path: (np.array([0.1], dtype=np.float32), 16000),
            )
            monkeypatch.setattr(
                "local_ai.slices.voice.transcribe_uploaded_media.service.create_audio_preprocessor",
                _raise_invalid_vad,
            )
            asyncio.run(
                transcribe_uploaded_media(
                    request=TranscribeUploadedMediaRequest(source_name="bad.wav", mime_type="audio/wav", payload=b"abc", vad_mode=8),
                    pipe=object(),
                    generate_kwargs={},
                    infer_lock=asyncio.Lock(),
                    logger=lambda *args: None,
                    start_time=0.0,
                    verbose=False,
                    likely_reason_details_fn=lambda exc: ["detail"],
                    to_thread_fn=asyncio.to_thread,
                )
            )

    assert exc_info.value.status_code == 422
