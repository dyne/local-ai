from __future__ import annotations

import argparse
from types import SimpleNamespace

import local_ai_voice


def test_run_file_mode_uses_runtime_error_details_and_prints_result(monkeypatch, capsys) -> None:
    captured_details: list[object] = []

    def fake_execute_transcribe_file(**kwargs):
        captured_details.append(kwargs["runtime_error_details"])
        return SimpleNamespace(exit_code=0, text="hello", reason=None, details=None)

    monkeypatch.setattr(local_ai_voice, "execute_transcribe_file", fake_execute_transcribe_file)

    result = local_ai_voice.run_file_mode(
        argparse.Namespace(input_path="sample.mp4", verbose=False),
        pipe=object(),
        audio_preprocessor=None,
        generate_kwargs={},
        start=0.0,
    )

    assert result == 0
    assert captured_details == [local_ai_voice.likely_reason_details]
    assert capsys.readouterr().out == "hello\n"
