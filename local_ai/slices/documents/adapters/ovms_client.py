from __future__ import annotations

import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def _default_http_get(url: str, timeout_seconds: int) -> tuple[int, str]:
    request = Request(url=url, method="GET")
    with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
        body = response.read().decode("utf-8")
        return int(response.status), body


class OvmsClient:
    """Lightweight OVMS health and model metadata client."""

    def __init__(
        self,
        *,
        base_url: str,
        config_path: Path,
        setup_command: str,
        timeout_seconds: int = 3,
        http_get_fn: object | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._config_path = config_path
        self._setup_command = setup_command
        self._timeout_seconds = timeout_seconds
        self._http_get_fn = http_get_fn or _default_http_get

    def list_configured_models_from_file(self) -> tuple[str, ...]:
        if not self._config_path.exists():
            return ()
        payload = json.loads(self._config_path.read_text(encoding="utf-8"))
        names: list[str] = []
        for item in payload.get("model_config_list", []):
            config = item.get("config", {})
            name = config.get("name")
            if isinstance(name, str) and name:
                names.append(name)
        return tuple(names)

    def health(self, *, embedding_model: str, generation_model: str | None) -> dict[str, object]:
        configured = self.list_configured_models_from_file()
        embedding_ready = embedding_model in configured
        generation_ready = generation_model in configured if generation_model else False
        details: dict[str, object] = {
            "base_url": self._base_url,
            "configured_models": configured,
            "embedding_model": embedding_model,
            "generation_model": generation_model,
            "embedding_model_ready": embedding_ready,
            "generation_model_ready": generation_ready,
            "setup_command": self._setup_command,
        }
        try:
            status_code, _ = self._http_get_fn(f"{self._base_url}/v1/config", self._timeout_seconds)
            details["status_code"] = status_code
            details["status"] = "ready" if status_code < 500 else "error"
        except URLError as exc:
            details["status"] = "unavailable"
            details["error"] = str(exc)
        except Exception as exc:  # pragma: no cover - defensive catch for custom http clients
            details["status"] = "error"
            details["error"] = str(exc)
        return details
