from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from local_ai.slices.documents.request import AddSourceRequest, IndexSourceRequest, QueryDocumentsRequest

_LOG = logging.getLogger(__name__)


def register_documents_routes(app: FastAPI, *, bundle: object) -> None:
    """Register documents HTTP routes using the provided service bundle."""

    @app.get("/api/documents/status")
    async def documents_status() -> JSONResponse:
        response = bundle.status_service.execute(  # type: ignore[attr-defined]
            embedding_model=bundle.config.embedding_model_name,  # type: ignore[attr-defined]
            generation_model=bundle.config.generation_model_name,  # type: ignore[attr-defined]
        )
        payload = response.to_dict()
        ovms = ((payload.get("health") or {}).get("ovms") if isinstance(payload.get("health"), dict) else None)  # type: ignore[union-attr]
        if isinstance(ovms, dict) and ovms.get("status") in {"unavailable", "error"}:
            _LOG.warning("Documents OVMS unavailable in /api/documents/status: %s", ovms)
        return JSONResponse(payload)

    @app.post("/api/documents/sources")
    async def add_documents_source(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
            parsed = AddSourceRequest(**payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc
        try:
            response = bundle.add_source_service.execute(parsed)  # type: ignore[attr-defined]
        except Exception as exc:
            _LOG.exception("Documents add-source failed.")
            raise HTTPException(status_code=500, detail="Documents source registration failed.") from exc
        status_code = 200 if response.status == "ok" else 400
        if status_code >= 400:
            _LOG.warning("Documents add-source validation failed: %s", response.to_dict())
        return JSONResponse(response.to_dict(), status_code=status_code)

    @app.post("/api/documents/index")
    async def index_documents(request: Request) -> JSONResponse:
        try:
            payload = await request.json() if request.headers.get("content-length") not in (None, "0") else {}
            parsed = IndexSourceRequest(**payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc
        try:
            response = bundle.index_documents_service.execute(parsed)  # type: ignore[attr-defined]
        except Exception as exc:
            _LOG.exception("Documents index failed.")
            raise HTTPException(status_code=500, detail="Documents indexing failed. Check Recoll logs and health endpoints.") from exc
        status_code = 200 if response.status in {"success", "ok"} else 400
        if status_code >= 400:
            _LOG.warning("Documents index returned non-success response: %s", response.to_dict())
        return JSONResponse(response.to_dict(), status_code=status_code)

    @app.post("/api/documents/query")
    async def query_documents(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
            parsed = QueryDocumentsRequest(**payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc
        try:
            response = bundle.query_documents_service.execute(parsed)  # type: ignore[attr-defined]
        except Exception as exc:
            _LOG.exception("Documents query failed.")
            raise HTTPException(status_code=500, detail="Documents query failed. Check Documents health endpoints.") from exc
        return JSONResponse(response.to_dict(), status_code=200)

    @app.get("/api/documents/{document_id}")
    async def get_document(document_id: str) -> JSONResponse:
        if not document_id.strip():
            raise HTTPException(status_code=400, detail="document_id must be non-empty.")
        doc_ref = bundle.repository.get_document_ref(document_id)  # type: ignore[attr-defined]
        if doc_ref is None:
            raise HTTPException(status_code=404, detail="Unknown document id.")
        candidate = type(
            "_Candidate",
            (),
            {
                "document_id": doc_ref.document_id,
                "source_path": doc_ref.source_path,
                "title": doc_ref.title,
                "snippet": "",
                "lexical_rank": 0,
            },
        )()
        text = bundle.text_loader.load_candidate_text(candidate)  # type: ignore[attr-defined]
        return JSONResponse(
            {
                "status": "ok",
                "document": {
                    "document_id": doc_ref.document_id,
                    "source_id": doc_ref.source_id,
                    "source_path": doc_ref.source_path,
                    "title": doc_ref.title,
                    "mime_type": doc_ref.mime_type,
                    "text": text.text,
                    "warning": text.warning,
                },
            }
        )

    @app.get("/api/documents/health/recoll")
    async def documents_recoll_health() -> JSONResponse:
        return JSONResponse(bundle.lexical_index.health())  # type: ignore[attr-defined]

    @app.get("/api/documents/health/ovms")
    async def documents_ovms_health() -> JSONResponse:
        payload = bundle.ovms_client.health(  # type: ignore[attr-defined]
            embedding_model=bundle.config.embedding_model_name,  # type: ignore[attr-defined]
            generation_model=bundle.config.generation_model_name,  # type: ignore[attr-defined]
        )
        if payload.get("status") in {"unavailable", "error"}:
            _LOG.warning("Documents OVMS health unavailable: %s", payload)
        return JSONResponse(payload)

    @app.get("/api/documents/health/redis")
    async def documents_redis_health() -> JSONResponse:
        payload = bundle.vector_index.health()  # type: ignore[attr-defined]
        return JSONResponse(payload)
