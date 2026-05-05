from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    """Output of one subprocess invocation."""

    returncode: int
    stdout: str
    stderr: str
    elapsed_ms: int


class SubprocessCommandRunner:
    """Thin wrapper around subprocess.run for adapter boundaries."""

    def run(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        extra_path_entries: tuple[Path, ...] = (),
        extra_env: dict[str, str] | None = None,
        timeout_seconds: int = 120,
    ) -> CommandResult:
        env = os.environ.copy()
        if extra_path_entries:
            prefix = os.pathsep.join(str(entry) for entry in extra_path_entries)
            env["PATH"] = f"{prefix}{os.pathsep}{env.get('PATH', '')}"
        if extra_env:
            env.update(extra_env)
        started = time.monotonic()
        completed = subprocess.run(  # noqa: S603
            command,
            cwd=str(cwd) if cwd else None,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
        elapsed_ms = int((time.monotonic() - started) * 1000)
        return CommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_ms=elapsed_ms,
        )
