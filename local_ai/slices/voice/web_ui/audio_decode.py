from __future__ import annotations

from typing import Callable

import av

from local_ai.slices.voice.shared.media_decode import decode_audio_frame, decode_media_bytes
from local_ai.slices.voice.web_ui.server_config import mime_type_to_av_format


def try_decode_bytes(
    *,
    payload: bytes,
    mime_type: str | None,
    open_container: Callable[..., object] = av.open,
) -> tuple[np.ndarray, int] | None:
    format_hint = mime_type_to_av_format(mime_type)
    return decode_media_bytes(payload, format_hint=format_hint, open_container=open_container)
