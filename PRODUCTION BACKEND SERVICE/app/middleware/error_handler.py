"""
backend/app/middleware/error_handler.py
Global exception handlers preventing stack trace leakage in production.
Formats errors into RFC 7807 standardized JSON problem envelopes.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("airo2.errors")


def register_error_handlers(app: FastAPI) -> None:
    """Registers standard institutional error handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc):
        req_id = getattr(request.state, "request_id", "n/a")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": exc.status_code,
                "error": "HTTPException",
                "message": exc.detail,
                "path": request.url.path,
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        req_id = getattr(request.state, "request_id", "n/a")
        logger.warning(f"[Security] Request validation failed on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=422,
            content={
                "status": 422,
                "error": "UnprocessableEntity",
                "message": "Input validation error in parameters or payload schema.",
                "details": [
                    {"loc": err.get("loc", []), "msg": err.get("msg", ""), "type": err.get("type", "")}
                    for err in exc.errors()
                ],
                "path": request.url.path,
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id}
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        req_id = getattr(request.state, "request_id", "n/a")
        logger.error(f"[Critical] Unhandled server exception on {request.url.path} (req_id={req_id}): {exc}", exc_info=True)
        
        # Never leak raw python tracebacks to client in production
        return JSONResponse(
            status_code=500,
            content={
                "status": 500,
                "error": "InternalServerError",
                "message": "An internal error occurred while processing the atmospheric forecast. Our operations team has been notified.",
                "path": request.url.path,
                "request_id": req_id,
            },
            headers={"X-Request-ID": req_id}
        )
