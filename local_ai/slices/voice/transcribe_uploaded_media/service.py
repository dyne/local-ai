from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Callable

import numpy as np

from local_ai.slices.voice.shared.audio_processing import (
    AudioPreprocessor,
    create_audio_preprocessor,
    ensure_sample_rate,
    preprocess_audio,
)
from local_ai.slices.voice.shared.media_decode import decode_media_file
from local_ai.slices.voice.shared.transcript_policy import should_suppress_transcript, transcribe_chunk
from local_ai.slices.voice.transcribe_uploaded_media.request import TranscribeUploadedMediaRequest
from local_ai.slices.voice.transcribe_uploaded_media.response import TranscribeUploadedMediaResponse

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@dataclass
class UploadedMediaError(Exception):
    """Domain error with an HTTP-ready status and concise diagnostics."""

    status_code: int
    reason: str
    details: list[str]


async def transcribe_uploaded_media(
    *,
    request: TranscribeUploadedMediaRequest,
    pipe: object,
    generate_kwargs: dict[str, object],
    infer_lock: object,
    logger: Callable[[str, bool, float | None], None],
    start_time: float,
    verbose: bool,
    likely_reason_details_fn: Callable[[Exception], list[str] | tuple[str, ...]],
    to_thread_fn: Callable[..., object],
) -> TranscribeUploadedMediaResponse:
    if not request.payload:
        raise UploadedMediaError(400, "Upload is empty.", ["No file bytes were provided."])
    if len(request.payload) > MAX_UPLOAD_BYTES:
        raise UploadedMediaError(413, "Upload too large.", [f"Max upload size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB."])

    suffix = Path(request.source_name).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
        temp_path = Path(handle.name)
        handle.write(request.payload)

    try:
        try:
            audio, sample_rate = decode_media_file(temp_path)
        except ValueError as exc:
            raise UploadedMediaError(422, "No decodable audio stream found.", [str(exc)]) from exc
        except Exception as exc:  # pragma: no cover
            raise UploadedMediaError(422, "Media decode failed.", [f"Runtime error: {exc}"]) from exc

        try:
            preprocessor: AudioPreprocessor | None = create_audio_preprocessor(
                request.silence_detect,
                vad_mode=request.vad_mode,
            )
        except Exception as exc:
            raise UploadedMediaError(500, "Audio preprocessing setup failed.", [f"Runtime error: {exc}"]) from exc
        audio = preprocess_audio(audio, sample_rate, preprocessor, verbose, start_time, logger)
        if audio.size == 0:
            raise UploadedMediaError(422, "No speech detected.", ["Input appears silent after preprocessing."])
        audio, sample_rate = ensure_sample_rate(audio, sample_rate, verbose, start_time, logger)
        duration_seconds = audio.shape[0] / float(sample_rate) if sample_rate > 0 else 0.0

        try:
            async with infer_lock:
                text = await to_thread_fn(transcribe_chunk, pipe, audio, generate_kwargs)
        except Exception as exc:
            details = list(likely_reason_details_fn(exc)) or [f"Runtime error: {exc}"]
            raise UploadedMediaError(500, "Transcription failed.", details) from exc

        if should_suppress_transcript(text, preprocessor):
            raise UploadedMediaError(422, "No speech detected.", ["Input appears to contain only weak non-speech noise."])

        return TranscribeUploadedMediaResponse(
            text=text,
            duration_seconds=duration_seconds,
            sample_rate=sample_rate,
            source_name=request.source_name,
        )
    finally:
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass
