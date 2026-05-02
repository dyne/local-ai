from __future__ import annotations

import pathlib

import numpy as np
import pytest

from local_ai.slices.voice.shared.media_decode import decode_audio_frame, decode_media_file


class FakeFrame:
    def __init__(self, array: np.ndarray, sample_rate: int) -> None:
        self._array = array
        self.sample_rate = sample_rate

    def to_ndarray(self) -> np.ndarray:
        return self._array


def test_decode_audio_frame_downmixes_and_scales_integer_audio() -> None:
    frame = FakeFrame(np.array([[0, 32767], [0, 32767]], dtype=np.int16), 16000)

    audio = decode_audio_frame(frame)

    assert audio.dtype == np.float32
    assert audio.tolist() == pytest.approx([0.0, 1.0], rel=1e-4)


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
