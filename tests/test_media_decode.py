from __future__ import annotations

import pathlib

import numpy as np
import pytest

from local_ai.slices.voice.shared.media_decode import decode_audio_frame, decode_media_file


class FakeFrame:
    class _Layout:
        def __init__(self, channels: int) -> None:
            self.channels = [object() for _ in range(channels)]
            self.nb_channels = channels

    def __init__(self, array: np.ndarray, sample_rate: int, channels: int = 1) -> None:
        self._array = array
        self.sample_rate = sample_rate
        self.layout = self._Layout(channels)

    def to_ndarray(self) -> np.ndarray:
        return self._array


def test_decode_audio_frame_downmixes_and_scales_integer_audio() -> None:
    frame = FakeFrame(np.array([[0, 32767], [0, 32767]], dtype=np.int16), 16000)

    audio = decode_audio_frame(frame)

    assert audio.dtype == np.float32
    assert audio.tolist() == pytest.approx([0.0, 1.0], rel=1e-4)


def test_decode_audio_frame_downmixes_packed_stereo_interleaved_audio() -> None:
    frame = FakeFrame(np.array([[32767, -32768, -32768, 32767]], dtype=np.int16), 16000, channels=2)

    audio = decode_audio_frame(frame)

    assert audio.dtype == np.float32
    assert audio.tolist() == pytest.approx([-1.5258789e-05, -1.5258789e-05], rel=1e-4, abs=1e-6)


def test_decode_audio_frame_offsets_unsigned_integer_audio_before_scaling() -> None:
    frame = FakeFrame(np.array([0, 128, 255], dtype=np.uint8), 16000)

    audio = decode_audio_frame(frame)

    assert audio.dtype == np.float32
    assert audio.tolist() == pytest.approx([-1.0, 0.0, 0.9921875], rel=1e-4, abs=1e-6)


def test_decode_media_file_concatenates_decoded_frames(tmp_path: pathlib.Path) -> None:
    media_path = tmp_path / "sample.mp3"
    media_path.write_bytes(b"stub")
    frames = [
        FakeFrame(np.array([[0, 32767]], dtype=np.int16), 16000),
        FakeFrame(np.array([[32767, 0]], dtype=np.int16), 16000),
    ]

    class FakeContainer:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def decode(self, audio: int):
            return iter(frames)

    result = decode_media_file(media_path, open_container=lambda source: FakeContainer())

    audio, sample_rate = result
    assert sample_rate == 16000
    assert audio.tolist() == pytest.approx([0.0, 1.0, 1.0, 0.0], rel=1e-4)


def test_decode_media_file_raises_when_no_audio_stream(tmp_path: pathlib.Path) -> None:
    media_path = tmp_path / "sample.mp4"
    media_path.write_bytes(b"stub")

    class FakeContainer:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def decode(self, audio: int):
            return iter([])

    with pytest.raises(ValueError, match="No decodable audio stream found"):
        decode_media_file(media_path, open_container=lambda source: FakeContainer())


def test_decode_audio_frame_clips_float_values() -> None:
    frame = FakeFrame(np.array([1.3, -1.6, 0.25], dtype=np.float32), 16000)

    audio = decode_audio_frame(frame)

    assert audio.tolist() == pytest.approx([1.0, -1.0, 0.25], rel=1e-5)


def test_decode_audio_frame_handles_empty_frame() -> None:
    frame = FakeFrame(np.array([], dtype=np.int16), 16000)
    audio = decode_audio_frame(frame)
    assert audio.size == 0
