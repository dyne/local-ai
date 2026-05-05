from __future__ import annotations

import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def _http_ready(base_url: str, timeout_seconds: int) -> bool:
    request = Request(url=f"{base_url.rstrip('/')}/v1/config", method="GET")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            return int(response.status) < 500
    except URLError:
        return False
    except Exception:
        return False


class OvmsProcessManager:
    """Starts/stops local OVMS process for Documents when needed."""

    def __init__(
        self,
        *,
        base_url: str,
        setupvars_path: Path,
        config_path: Path,
        autostart: bool = True,
        startup_timeout_seconds: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._setupvars_path = setupvars_path
        self._config_path = config_path
        self._autostart = autostart
        self._startup_timeout_seconds = startup_timeout_seconds
        self._process: subprocess.Popen[str] | None = None
        self._started_by_local_ai = False

    def startup(self) -> None:
        if not self._autostart:
            return
        if _http_ready(self._base_url, timeout_seconds=2):
            return
        ovms_root = self._setupvars_path.parent.parent
        setupvars = self._setupvars_path.name
        command = (
            f"Set-Location '{ovms_root}'; "
            f".\\ovms\\{setupvars}; "
            f"ovms --rest_port 8080 --config_path '{self._config_path}'"
        )
        creationflags = 0
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
        self._process = subprocess.Popen(  # noqa: S603
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            cwd=str(ovms_root),
            creationflags=creationflags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        self._started_by_local_ai = True

        deadline = time.monotonic() + self._startup_timeout_seconds
        while time.monotonic() < deadline:
            if _http_ready(self._base_url, timeout_seconds=2):
                return
            if self._process.poll() is not None:
                break
            time.sleep(0.5)

    def shutdown(self) -> None:
        if not self._started_by_local_ai:
            return
        process = self._process
        self._process = None
        self._started_by_local_ai = False
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
