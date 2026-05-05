from __future__ import annotations

from pathlib import Path

import local_ai.slices.documents.adapters.ovms_lifecycle as lifecycle


def test_startup_skips_when_already_ready(monkeypatch) -> None:
    monkeypatch.setattr(lifecycle, "_http_ready", lambda *args, **kwargs: True)
    called = {"value": False}

    class _Popen:
        def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            called["value"] = True

    monkeypatch.setattr(lifecycle.subprocess, "Popen", _Popen)
    manager = lifecycle.OvmsProcessManager(
        base_url="http://127.0.0.1:8080",
        setupvars_path=Path("C:/llm/ovms/setupvars.ps1"),
        config_path=Path("C:/llm/models/config.json"),
    )
    manager.startup()
    assert called["value"] is False


def test_shutdown_terminates_started_process(monkeypatch) -> None:
    sequence = iter([False, True])
    monkeypatch.setattr(lifecycle, "_http_ready", lambda *args, **kwargs: next(sequence))
    monkeypatch.setattr(lifecycle.time, "sleep", lambda *args, **kwargs: None)

    class _Proc:
        def __init__(self):
            self.terminated = False

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout):  # type: ignore[no-untyped-def]
            return 0

    proc = _Proc()
    monkeypatch.setattr(lifecycle.subprocess, "Popen", lambda *args, **kwargs: proc)
    manager = lifecycle.OvmsProcessManager(
        base_url="http://127.0.0.1:8080",
        setupvars_path=Path("C:/llm/ovms/setupvars.ps1"),
        config_path=Path("C:/llm/models/config.json"),
    )
    manager.startup()
    manager.shutdown()
    assert proc.terminated is True
