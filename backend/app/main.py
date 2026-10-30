"""Local synthetic verification API. Simulated roles are not authentication."""

import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from .canonical import BadPackage
from .db import DEFAULT_DB, Database
from .multipart import read_package
from .schemas import AuditEvent, Laboratory, Status, VerificationResult
from .verification import verify_and_record

logger = logging.getLogger("rapidready")
ALLOWED_ORIGINS = {"http://127.0.0.1:5173", "http://localhost:5173",
                   "http://127.0.0.1:8000", "http://localhost:8000", "http://testserver"}


def create_app(database: Database | None = None) -> FastAPI:
    db = database or Database(Path(os.environ.get("RAPIDREADY_DB", str(DEFAULT_DB))))

    @asynccontextmanager
    async def lifespan(_app):
        db.initialize()
        yield

    app = FastAPI(title="RapidReady Verify", version="0.1.0", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)
    app.state.db = db

    def error(request, status, code, message, audit_recorded=False):
        return JSONResponse(status_code=status, content={"error": {
            "code": code, "message": message,
            "request_id": getattr(request.state, "request_id", "unassigned"),
            "audit_recorded": audit_recorded,
        }})

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        request.state.request_id = str(uuid4())
        origin = request.headers.get("origin")
        if request.url.hostname not in {"127.0.0.1", "localhost", "testserver"}:
            response = error(request, 400, "BAD_REQUEST", "Only local hostnames are supported.")
        elif origin is not None and origin not in ALLOWED_ORIGINS:
            response = error(request, 403, "FORBIDDEN", "This browser origin is not allowed.")
        else:
            try:
                response = await call_next(request)
            except Exception as exc:
                logger.error("Request %s failed: %s", request.state.request_id, type(exc).__name__)
                recorded = False
                try:
                    await run_in_threadpool(db.record_transport_error, "INTERNAL_ERROR", "Internal request failure.")
                    recorded = True
                except Exception:
                    logger.error("Request %s audit could not be persisted", request.state.request_id)
                response = error(request, 500, "INTERNAL_ERROR", "Verification could not be completed.", recorded)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(BadPackage)
    async def bad_package(request: Request, exc: BadPackage):
        try:
            await run_in_threadpool(db.record_transport_error, exc.code, exc.message)
        except sqlite3.Error:
            logger.error("Request %s rejection audit unavailable", request.state.request_id)
            return error(request, 503, "UNAVAILABLE", "Package rejected; audit storage is unavailable.")
        return error(request, exc.status, exc.code, exc.message, True)

    @app.exception_handler(sqlite3.Error)
    async def database_error(request: Request, _exc):
        logger.error("Request %s database operation failed", request.state.request_id)
        return error(request, 503, "UNAVAILABLE", "Storage is unavailable; no acceptance was recorded.")

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _exc):
        return error(request, 400, "BAD_REQUEST", "Invalid request parameters.")

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc):
        code = "NOT_FOUND" if exc.status_code == 404 else "BAD_REQUEST"
        return error(request, exc.status_code, code, "Resource or method is not available.")

    @app.get("/api/health")
    def health():
        ready = db.ready()
        return JSONResponse(status_code=200 if ready else 503, content={
            "status": "OK" if ready else "ERROR", "synthetic": True,
            "message": "Ready for synthetic verification." if ready else "Run the local demo preparation first.",
        })

    @app.post("/api/verify", response_model=VerificationResult)
    async def verify(request: Request):
        data, filename, manifest, signature = await read_package(request)
        return await run_in_threadpool(verify_and_record, db, data, filename, manifest, signature)

    @app.get("/api/verifications", response_model=list[VerificationResult])
    def verifications(status: Status | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 50):
        return db.list_results(status, limit)

    @app.get("/api/verifications/{verification_id}", response_model=VerificationResult)
    def verification(verification_id: str):
        result = db.get_result(verification_id)
        if result is None:
            raise HTTPException(404)
        return result

    @app.get("/api/audit", response_model=list[AuditEvent])
    def audit(verification_id: str | None = None, limit: Annotated[int, Query(ge=1, le=200)] = 100):
        return db.list_audit(verification_id, limit)

    @app.get("/api/laboratories", response_model=list[Laboratory])
    def laboratories():
        return db.list_laboratories()

    return app
