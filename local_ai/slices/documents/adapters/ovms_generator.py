from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


class GenerationUnavailableError(RuntimeError):
    """Raised when OVMS generation is not reachable or not configured."""


def _default_http_post(url: str, payload: dict[str, object], timeout_seconds: int) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url=url,
        method="POST",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        return int(response.status), response.read().decode("utf-8")


class OvmsTextGenerator:
    """Text generator adapter backed by OVMS OpenAI-compatible chat endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        model_name: str,
        setup_command: str,
        timeout_seconds: int = 30,
        http_post_fn: object | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._setup_command = setup_command
        self._timeout_seconds = timeout_seconds
        self._http_post_fn = http_post_fn or _default_http_post

    @property
    def model_id(self) -> str:
        return self._model_name

    def generate(self, *, query: str, context: str) -> str:
        payload = {
            "model": self._model_name,
            "messages": [
                {"role": "user", "content": context},
                {"role": "user", "content": f"Question: {query}"},
            ],
            "temperature": 0.0,
        }
        for endpoint in ("/v3/chat/completions", "/v1/chat/completions"):
            try:
                status, body = self._http_post_fn(f"{self._base_url}{endpoint}", payload, self._timeout_seconds)
            except URLError as exc:
                raise GenerationUnavailableError(
                    f"OVMS generation unavailable. Start OVMS with: {self._setup_command}"
                ) from exc
            if status == 404:
                continue
            if status >= 400:
                raise GenerationUnavailableError(f"OVMS generation request failed with HTTP {status}.")
            parsed = json.loads(body)
            choices = parsed.get("choices", [])
            if not choices:
                return ""
            message = choices[0].get("message", {})
            content = message.get("content")
            return str(content) if content is not None else ""
        raise GenerationUnavailableError("OVMS generation endpoint not found at /v3/chat/completions or /v1/chat/completions.")
