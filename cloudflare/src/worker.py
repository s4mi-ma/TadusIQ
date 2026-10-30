"""Hosted receiver: shared strict policy, native Ed25519, durable D1 audit."""
import logging
from typing import Annotated
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from js import crypto
from pyodide.ffi import to_js
from starlette.exceptions import HTTPException as StarletteHTTPException
from workers import asgi
from d1_store import D1Store, RESULT_SELECT, result_from_row
from shared.canonical import BadPackage
from shared.multipart import read_package
from shared.policy import PreparedPackage, decide
from shared.schemas import AuditEvent, Laboratory, Status, VerificationResult

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
logger = logging.getLogger("rapidready")

def store(request):
    return D1Store(request.scope["env"].DB)

def error(request, status, code, message, recorded=False):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message,
        "request_id": getattr(request.state, "request_id", "unassigned"), "audit_recorded": recorded}})

@app.middleware("http")
async def boundary(request: Request, call_next):
    request.state.request_id = str(uuid4())
    origin = request.headers.get("origin")
    expected_origin = str(request.base_url).rstrip("/")
    if origin is not None and origin != expected_origin:
        response = error(request, 403, "FORBIDDEN", "This browser origin is not allowed.")
    else:
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("Request %s failed: %s", request.state.request_id, type(exc).__name__)
            response = error(request, 503, "UNAVAILABLE", "Verification storage or runtime is unavailable; no completed decision was returned.")
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Request-ID"] = request.state.request_id
    return response

@app.exception_handler(BadPackage)
async def bad_package(request: Request, exc):
    try:
        await store(request).record_error(exc.code, exc.message)
    except Exception:
        return error(request, 503, "UNAVAILABLE", "Package rejected; audit storage is unavailable.")
    return error(request, exc.status, exc.code, exc.message, True)

@app.exception_handler(RequestValidationError)
async def invalid_query(request: Request, exc):
    return error(request, 400, "BAD_REQUEST", "Invalid request parameters.")

@app.exception_handler(StarletteHTTPException)
async def unavailable_route(request: Request, exc):
    return error(request, exc.status_code, "NOT_FOUND" if exc.status_code == 404 else "BAD_REQUEST", "Resource or method is not available.")

@app.get("/api/health")
async def health(request: Request):
    ready = await store(request).ready()
    return JSONResponse(status_code=200 if ready else 503, content={
        "status": "OK" if ready else "ERROR", "synthetic": True,
        "message": "Ready for synthetic verification." if ready else "Database and public key setup is required."})

@app.post("/api/verify", response_model=VerificationResult)
async def verify(request: Request):
    data, filename, raw, signature = await read_package(request)
    package = PreparedPackage(data, filename, raw, signature)
    db = store(request)
    key = await db.key(package.manifest.key_id) if package.valid_metadata else None
    valid = False
    if package.can_verify(key):
        imported = await crypto.subtle.importKey("raw", to_js(bytes.fromhex(key["public_key_hex"])),
                                                "Ed25519", False, to_js(["verify"]))
        valid = bool(await crypto.subtle.verify("Ed25519", imported, to_js(package.signature), to_js(raw)))
    result = decide(package, key, valid)
    await db.commit(result, package, key)
    return result

@app.get("/api/verifications", response_model=list[VerificationResult])
async def history(request: Request, status: Status | None = None, limit: Annotated[int, Query(ge=1, le=100)] = 50):
    rows = await store(request).rows(RESULT_SELECT + "WHERE (? IS NULL OR r.status=?) "
                                    "ORDER BY s.received_at DESC, s.verification_id DESC LIMIT ?", status, status, limit)
    return [result_from_row(row) for row in rows]

@app.get("/api/verifications/{verification_id}", response_model=VerificationResult)
async def detail(request: Request, verification_id: str):
    rows = await store(request).rows(RESULT_SELECT + "WHERE verification_id=?", verification_id)
    if not rows:
        raise HTTPException(404)
    return result_from_row(rows[0])

@app.get("/api/audit", response_model=list[AuditEvent])
async def audit(request: Request, verification_id: str | None = None, limit: Annotated[int, Query(ge=1, le=200)] = 100):
    return await store(request).rows("SELECT * FROM audit_events WHERE (? IS NULL OR verification_id=?) "
                                    "ORDER BY event_id DESC LIMIT ?", verification_id, verification_id, limit)

@app.get("/api/laboratories", response_model=list[Laboratory])
async def laboratories(request: Request):
    return await store(request).rows("SELECT * FROM laboratories ORDER BY laboratory_id")

Default = asgi.entrypoint(app)
