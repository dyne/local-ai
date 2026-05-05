from __future__ import annotations

import json
from math import sqrt
from urllib.error import URLError
from urllib.request import Request, urlopen

from local_ai.slices.documents.domain import Passage


class ModelUnavailableError(RuntimeError):
    """Raised when OVMS embedding model cannot be reached."""


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


class OvmsEmbeddingModel:
    """Embedding model adapter backed by OVMS OpenAI-compatible endpoints."""

    def __init__(
        self,
        *,
        base_url: str,
        model_name: str,
        setup_command: str,
        timeout_seconds: int = 10,
        batch_size: int = 16,
        http_post_fn: object | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model_name = model_name
        self._setup_command = setup_command
        self._timeout_seconds = timeout_seconds
        self._batch_size = max(1, batch_size)
        self._http_post_fn = http_post_fn or _default_http_post
        self._dimension: int | None = None

    @property
    def model_id(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension or 0

    def embed_query(self, query: str) -> tuple[float, ...]:
        if not query.strip():
            raise ValueError("Query must be non-empty for embeddings.")
        vectors = self._embed_batch((query,))
        return vectors[0]

    def embed_passages(self, passages: tuple[Passage, ...]) -> tuple[tuple[float, ...], ...]:
        if not passages:
            return ()
        chunks: list[tuple[float, ...]] = []
        texts = tuple(item.text for item in passages)
        for start in range(0, len(texts), self._batch_size):
            batch = texts[start : start + self._batch_size]
            chunks.extend(self._embed_batch(batch))
        return tuple(chunks)

    def _embed_batch(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        payload = {"model": self._model_name, "input": list(texts)}
        for endpoint in ("/v3/embeddings", "/v1/embeddings"):
            try:
                status, body = self._http_post_fn(f"{self._base_url}{endpoint}", payload, self._timeout_seconds)
            except URLError as exc:
                raise ModelUnavailableError(
                    f"OVMS embeddings unavailable. Start OVMS with: {self._setup_command}"
                ) from exc
            if status == 404:
                continue
            if status >= 400:
                raise ModelUnavailableError(f"OVMS embeddings request failed with HTTP {status}.")
            parsed = json.loads(body)
            data = parsed.get("data", [])
            vectors = [tuple(float(v) for v in item.get("embedding", [])) for item in data]
            if len(vectors) != len(texts):
                raise ModelUnavailableError("OVMS embeddings response size mismatch.")
            normalized = tuple(_normalize_vector(vector) for vector in vectors)
            if normalized:
                self._dimension = len(normalized[0])
            return normalized
        raise ModelUnavailableError("OVMS embeddings endpoint not found at /v3/embeddings or /v1/embeddings.")


def _normalize_vector(vector: tuple[float, ...]) -> tuple[float, ...]:
    if not vector:
        return vector
    norm = sqrt(sum(item * item for item in vector))
    if norm == 0.0:
        return vector
    return tuple(item / norm for item in vector)
