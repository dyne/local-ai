from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TextIO

from local_ai.shared.domain.log_events import LogEvent, LogLevel


@dataclass
class ConsoleAdapter:
    """Render structured log events to stderr/stdout with concise formatting."""

    stderr: TextIO = sys.stderr
    stdout: TextIO = sys.stdout

    def emit(self, event: LogEvent, *, verbose: bool = False) -> None:
        """Print event using severity-aware verbosity rules."""

        if event.level in (LogLevel.DEBUG, LogLevel.INFO) and not verbose:
            return

        line = f"[{event.timestamp}] {event.level.value} {event.source}: {event.message}"
        target = self.stderr if event.level in (LogLevel.ERROR, LogLevel.WARNING) else self.stdout
        print(line, file=target, flush=True)
        if event.details and (verbose or event.level is LogLevel.ERROR):
            for detail in event.details:
                print(f"- {detail}", file=target, flush=True)
