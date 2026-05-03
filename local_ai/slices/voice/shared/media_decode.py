from __future__ import annotations

from pathlib import Path
from typing import Callable
import io

import av
import numpy as np

from local_ai.slices.voice.shared.audio_processing import normalize_audio_format


def _frame_channel_count(frame: av.AudioFrame) -> int:
    layout = getattr(frame, "layout", None)
    if layout is None:
        return 1
    nb_channels = getattr(layout, "nb_channels", None)
    if isinstance(nb_channels, int) and nb_channels > 0:
        return nb_channels
    channels = getattr(layout, "channels", None)
    if channels is None:
        return 1
    try:
        count = len(channels)
    except TypeError:
        count = 0
    return count if count > 0 else 1


def decode_audio_frame(frame: av.AudioFrame) -> np.ndarray:
    array = frame.to_ndarray()
    if array.ndim == 2:
        if array.shape[0] > 1:
            audio = array.mean(axis=0)
        else:
            channels = _frame_channel_count(frame)
            if channels > 1 and array.shape[1] % channels == 0:
                audio = array.reshape(-1, channels).mean(axis=1)
            else:
                audio = array.reshape(-1)
    else:
        audio = array
    audio = normalize_audio_format(audio)
    if np.issubdtype(array.dtype, np.integer):
        type_info = np.iinfo(array.dtype)
        if np.issubdtype(array.dtype, np.unsignedinteger):
            midpoint = float(type_info.max // 2 + 1)
            audio = (audio - midpoint) / midpoint
        else:
            max_value = max(abs(type_info.min), type_info.max)
            audio = audio / float(max_value)
    return np.clip(audio, -1.0, 1.0).astype(np.float32, copy=False)


def decode_media_file(
    path: Path,
    *,
    open_container: Callable[..., object] = av.open,
) -> tuple[np.ndarray, int]:
    with open_container(str(path)) as container:
        decoded_frames: list[np.ndarray] = []
        sample_rate: int | None = None
        for frame in container.decode(audio=0):
            mono = decode_audio_frame(frame)
            if mono.size == 0:
                continue
            decoded_frames.append(mono)
            sample_rate = int(frame.sample_rate)
    if not decoded_frames or sample_rate is None:
        raise ValueError(f"No decodable audio stream found: {path}")
    return np.concatenate(decoded_frames), sample_rate


def decode_media_bytes(
    payload: bytes,
    *,
    format_hint: str | None = None,
    open_container: Callable[..., object] = av.open,
) -> tuple[np.ndarray, int] | None:
    with open_container(io.BytesIO(payload), format=format_hint) as container:
        decoded_frames: list[np.ndarray] = []
        sample_rate: int | None = None
        for frame in container.decode(audio=0):
            mono = decode_audio_frame(frame)
            if mono.size == 0:
                continue
            decoded_frames.append(mono)
            sample_rate = int(frame.sample_rate)
    if not decoded_frames or sample_rate is None:
        return None
    return np.concatenate(decoded_frames), sample_rate
