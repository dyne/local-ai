from __future__ import annotations

from pathlib import Path

from local_ai.slices.documents.domain import DocumentText, SearchCandidate

_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".rst",
    ".org",
    ".py",
    ".js",
    ".ts",
    ".svelte",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".csv",
    ".log",
    ".html",
}


class CandidateTextLoader:
    """Loads bounded text for lexical candidates using local filesystem fallback."""

    def __init__(self, *, max_characters: int = 500_000) -> None:
        self._max_characters = max_characters

    def load_candidate_text(self, candidate: SearchCandidate) -> DocumentText:
        path = Path(candidate.source_path)
        if not path.exists():
            return DocumentText(
                document_id=candidate.document_id,
                text="",
                warning="Candidate source file no longer exists on disk.",
            )
        if path.suffix.lower() not in _TEXT_EXTENSIONS:
            return DocumentText(
                document_id=candidate.document_id,
                text="",
                warning=f"Unsupported extension for direct text loading: {path.suffix or '<none>'}.",
            )
        payload = path.read_bytes()
        if b"\x00" in payload:
            return DocumentText(
                document_id=candidate.document_id,
                text="",
                warning="Binary-like payload detected while loading candidate text.",
            )
        decoded = _decode_payload(payload)
        if len(decoded) > self._max_characters:
            return DocumentText(
                document_id=candidate.document_id,
                text=decoded[: self._max_characters],
                warning=f"Text truncated to {self._max_characters} characters.",
            )
        return DocumentText(document_id=candidate.document_id, text=decoded)


def _decode_payload(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")
