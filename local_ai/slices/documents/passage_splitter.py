from __future__ import annotations

import hashlib
import re

from local_ai.slices.documents.domain import DocumentText, Passage


class DeterministicPassageSplitter:
    """Deterministic paragraph-first passage splitter with bounded fallback modes."""

    def __init__(
        self,
        *,
        target_chars: int = 1000,
        max_chars: int = 1200,
        overlap_chars: int = 120,
    ) -> None:
        self._target_chars = target_chars
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    def split(self, document: DocumentText, *, source_path: str) -> tuple[Passage, ...]:
        text = document.text
        if not text:
            return ()
        segments = _split_paragraphs(text)
        passages: list[Passage] = []
        current_start = 0
        current_text_parts: list[str] = []
        current_len = 0

        for segment_start, segment_text in segments:
            segment_len = len(segment_text)
            if segment_len > self._max_chars:
                if current_text_parts:
                    passages.append(self._build_passage(document.document_id, source_path, current_start, "".join(current_text_parts)))
                    current_text_parts = []
                    current_len = 0
                passages.extend(self._split_dense_segment(document.document_id, source_path, segment_start, segment_text))
                continue
            if not current_text_parts:
                current_start = segment_start
            if current_len + segment_len <= self._target_chars:
                current_text_parts.append(segment_text)
                current_len += segment_len
            else:
                passages.append(self._build_passage(document.document_id, source_path, current_start, "".join(current_text_parts)))
                current_text_parts = [segment_text]
                current_start = segment_start
                current_len = segment_len
        if current_text_parts:
            passages.append(self._build_passage(document.document_id, source_path, current_start, "".join(current_text_parts)))
        return tuple(passages)

    def _split_dense_segment(self, document_id: str, source_path: str, start_offset: int, text: str) -> list[Passage]:
        lines = text.splitlines(keepends=True)
        if len(lines) > 1:
            passages: list[Passage] = []
            running_start = start_offset
            current = ""
            for line in lines:
                if len(current) + len(line) > self._max_chars and current:
                    passages.append(self._build_passage(document_id, source_path, running_start, current))
                    running_start += len(current)
                    current = line
                else:
                    current += line
            if current:
                passages.append(self._build_passage(document_id, source_path, running_start, current))
            return passages
        return self._split_with_overlap(document_id, source_path, start_offset, text)

    def _split_with_overlap(self, document_id: str, source_path: str, start_offset: int, text: str) -> list[Passage]:
        step = max(1, self._max_chars - self._overlap_chars)
        passages: list[Passage] = []
        offset = 0
        while offset < len(text):
            chunk = text[offset : offset + self._max_chars]
            passages.append(self._build_passage(document_id, source_path, start_offset + offset, chunk))
            if offset + self._max_chars >= len(text):
                break
            offset += step
        return passages

    @staticmethod
    def _build_passage(document_id: str, source_path: str, start_offset: int, text: str) -> Passage:
        digest = hashlib.sha256(f"{document_id}:{start_offset}:{text}".encode("utf-8")).hexdigest()[:16]
        end_offset = start_offset + len(text)
        return Passage(
            passage_id=digest,
            document_id=document_id,
            source_path=source_path,
            text=text,
            start_offset=start_offset,
            end_offset=end_offset,
        )


def _split_paragraphs(text: str) -> list[tuple[int, str]]:
    parts: list[tuple[int, str]] = []
    for match in re.finditer(r".*?(?:\n\s*\n|$)", text, flags=re.DOTALL):
        chunk = match.group(0)
        if not chunk:
            continue
        parts.append((match.start(), chunk))
    return parts
