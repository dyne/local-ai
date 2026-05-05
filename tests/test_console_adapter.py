from __future__ import annotations

from io import StringIO

from local_ai.shared.domain.log_events import LogEvent, LogLevel
from local_ai.shared.logging.console_adapter import ConsoleAdapter


def test_console_adapter_prints_error_without_verbose() -> None:
    stderr = StringIO()
    adapter = ConsoleAdapter(stderr=stderr, stdout=StringIO())

    adapter.emit(LogEvent.create(level=LogLevel.ERROR, source="voice.runtime", message="failed", details=["x"]), verbose=False)

    output = stderr.getvalue()
    assert "ERROR voice.runtime: failed" in output
    assert "- x" in output


def test_console_adapter_hides_info_when_not_verbose() -> None:
    stdout = StringIO()
    adapter = ConsoleAdapter(stderr=StringIO(), stdout=stdout)

    adapter.emit(LogEvent.create(level=LogLevel.INFO, source="voice.runtime", message="ok"), verbose=False)

    assert stdout.getvalue() == ""
