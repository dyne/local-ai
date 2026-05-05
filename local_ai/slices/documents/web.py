from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from local_ai.slices.documents.request import AddSourceRequest, IndexSourceRequest


def register_documents_routes(app: FastAPI, *, bundle: object) -> None:
    """Register documents HTTP routes using the provided service bundle."""

    @app.get("/api/documents/status")
    async def documents_status() -> JSONResponse:
        response = bundle.status_service.execute(  # type: ignore[attr-defined]
            embedding_model=bundle.config.embedding_model_name,  # type: ignore[attr-defined]
            generation_model=bundle.config.generation_model_name,  # type: ignore[attr-defined]
        )
        return JSONResponse(response.to_dict())

    @app.post("/api/documents/sources")
    async def add_documents_source(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
            parsed = AddSourceRequest(**payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body.") from exc
        response = bundle.add_source_service.execute(parsed)  # type: ignore[attr-defined]
        status_code = 200 if response.status == "ok" else 400
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
        response = bundle.index_documents_service.execute(parsed)  # type: ignore[attr-defined]
        status_code = 200 if response.status in {"success", "ok"} else 400
        return JSONResponse(response.to_dict(), status_code=status_code)

    @app.get("/api/documents/health/recoll")
    async def documents_recoll_health() -> JSONResponse:
        return JSONResponse(bundle.lexical_index.health())  # type: ignore[attr-defined]

    @app.get("/api/documents/health/ovms")
    async def documents_ovms_health() -> JSONResponse:
        payload = bundle.ovms_client.health(  # type: ignore[attr-defined]
            embedding_model=bundle.config.embedding_model_name,  # type: ignore[attr-defined]
            generation_model=bundle.config.generation_model_name,  # type: ignore[attr-defined]
        )
        return JSONResponse(payload)

    @app.get("/api/documents/health/redis")
    async def documents_redis_health() -> JSONResponse:
        return JSONResponse(
            {
                "status": "not_configured",
                "redis_url": bundle.config.redis_url,  # type: ignore[attr-defined]
                "index_name": bundle.config.redis_index_name,  # type: ignore[attr-defined]
            }
        )
