from __future__ import annotations

import pathlib

import numpy as np

from local_ai.slices.voice.transcribe_file.request import TranscribeFileRequest
from local_ai.slices.voice.transcribe_file.service import execute_transcribe_file


def test_execute_transcribe_file_returns_missing_file_error(tmp_path: pathlib.Path) -> None:
    response = execute_transcribe_file(
        request=TranscribeFileRequest(input_path=tmp_path / "missing.wav", verbose=False),
        pipe=object(),
        audio_preprocessor=None,
        generate_kwargs={},
        start=0.0,
        logger=lambda message, verbose, start: None,
        runtime_error_details=lambda exc: [str(exc)],
    )

    assert response.exit_code == 2
    assert response.reason == f"Input file not found: {tmp_path / 'missing.wav'}"


def test_execute_transcribe_file_returns_success(monkeypatch, tmp_path: pathlib.Path) -> None:
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(b"stub")
    messages: list[str] = []
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.decode_media_file",
        lambda path: (np.array([0.1, -0.2], dtype=np.float32), 16000),
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.preprocess_audio",
        lambda audio, sample_rate, preprocessor, verbose, start, logger: audio,
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.ensure_sample_rate",
        lambda audio, sample_rate, verbose, start, logger: (audio, sample_rate),
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.transcribe_chunk",
        lambda pipe, audio, kwargs: "hello",
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.should_suppress_transcript",
        lambda text, preprocessor: False,
    )

    response = execute_transcribe_file(
        request=TranscribeFileRequest(input_path=wav_path, verbose=True),
        pipe=object(),
        audio_preprocessor=None,
        generate_kwargs={},
        start=0.0,
        logger=lambda message, verbose, start: messages.append(message),
        runtime_error_details=lambda exc: [str(exc)],
    )

    assert response.exit_code == 0
    assert response.text == "hello"
    assert messages == [
        "Decoding input media",
        "Decoded audio: samples=2, sample_rate=16000 Hz, duration=0.00s",
        "Starting audio preprocessing",
        "Audio prepared: samples=2, sample_rate=16000 Hz",
        "Starting Whisper inference",
    ]


def test_execute_transcribe_file_returns_preprocessing_error(monkeypatch, tmp_path: pathlib.Path) -> None:
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(b"stub")
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.decode_media_file",
        lambda path: (np.array([0.1], dtype=np.float32), 16000),
    )

    def raise_preprocess(audio, sample_rate, preprocessor, verbose, start, logger):
        raise RuntimeError("bad preprocess")

    monkeypatch.setattr("local_ai.slices.voice.transcribe_file.service.preprocess_audio", raise_preprocess)

    response = execute_transcribe_file(
        request=TranscribeFileRequest(input_path=wav_path, verbose=False),
        pipe=object(),
        audio_preprocessor=None,
        generate_kwargs={},
        start=0.0,
        logger=lambda message, verbose, start: None,
        runtime_error_details=lambda exc: [str(exc)],
    )

    assert response.exit_code == 6
    assert response.reason == "Audio preprocessing failed."


def test_execute_transcribe_file_returns_suppressed_noise(monkeypatch, tmp_path: pathlib.Path) -> None:
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(b"stub")
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.decode_media_file",
        lambda path: (np.array([0.1], dtype=np.float32), 16000),
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.preprocess_audio",
        lambda audio, sample_rate, preprocessor, verbose, start, logger: audio,
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.ensure_sample_rate",
        lambda audio, sample_rate, verbose, start, logger: (audio, sample_rate),
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.transcribe_chunk",
        lambda pipe, audio, kwargs: "uh",
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.should_suppress_transcript",
        lambda text, preprocessor: True,
    )

    response = execute_transcribe_file(
        request=TranscribeFileRequest(input_path=wav_path, verbose=False),
        pipe=object(),
        audio_preprocessor=None,
        generate_kwargs={},
        start=0.0,
        logger=lambda message, verbose, start: None,
        runtime_error_details=lambda exc: [str(exc)],
    )

    assert response.exit_code == 2
    assert response.reason == "No speech detected."


def test_execute_transcribe_file_returns_runtime_error_details(monkeypatch, tmp_path: pathlib.Path) -> None:
    wav_path = tmp_path / "sample.wav"
    wav_path.write_bytes(b"stub")
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.decode_media_file",
        lambda path: (np.array([0.1], dtype=np.float32), 16000),
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.preprocess_audio",
        lambda audio, sample_rate, preprocessor, verbose, start, logger: audio,
    )
    monkeypatch.setattr(
        "local_ai.slices.voice.transcribe_file.service.ensure_sample_rate",
        lambda audio, sample_rate, verbose, start, logger: (audio, sample_rate),
    )

    def raise_transcribe(pipe, audio, kwargs):
        raise RuntimeError("bad inference")

    monkeypatch.setattr("local_ai.slices.voice.transcribe_file.service.transcribe_chunk", raise_transcribe)

    response = execute_transcribe_file(
        request=TranscribeFileRequest(input_path=wav_path, verbose=False),
        pipe=object(),
        audio_preprocessor=None,
        generate_kwargs={},
        start=0.0,
        logger=lambda message, verbose, start: None,
        runtime_error_details=lambda exc: [f"Runtime error: {exc}"],
    )

    assert response.exit_code == 5
    assert response.reason == "Transcription failed."
    assert response.details == ["Runtime error: bad inference"]


def test_execute_transcribe_file_returns_decode_error(monkeypatch, tmp_path: pathlib.Path) -> None:
    media_path = tmp_path / "sample.mp3"
    media_path.write_bytes(b"stub")

    def raise_decode(path: pathlib.Path) -> tuple[np.ndarray, int]:
        raise ValueError("bad media")

    monkeypatch.setattr("local_ai.slices.voice.transcribe_file.service.decode_media_file", raise_decode)

    response = execute_transcribe_file(
        request=TranscribeFileRequest(input_path=media_path, verbose=False),
        pipe=object(),
        audio_preprocessor=None,
        generate_kwargs={},
        start=0.0,
        logger=lambda message, verbose, start: None,
        runtime_error_details=lambda exc: [str(exc)],
    )

    assert response.exit_code == 2
    assert response.reason == "Audio decode failed."
    assert response.details == ["Runtime error: bad media"]
