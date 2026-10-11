"""One error shape for every failure, so the page and every client handle errors the same way:

    {"code": "not_found", "message": "Not found.", "request_id": "3f2a..."}

`code` is for programs (it never changes), `message` is for people. Validation errors add
`details` (which field, and why). An unexpected error never shows its text or a stack trace:
the logs have it, under the same request_id.
"""

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .db import DatabaseUnavailable

logger = logging.getLogger("doc_assistant")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, headers: dict | None = None,
                 details: list | None = None):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message
        self.headers, self.details = headers or {}, details


def not_found() -> ApiError:
    """The same answer for "it does not exist" and "it is another shop's": nothing leaks."""
    return ApiError(404, "not_found", "Not found.")


def request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None)
    if rid is None:
        rid = request.state.request_id = uuid.uuid4().hex[:16]
    return rid


def body(request: Request, code: str, message: str, details: list | None = None) -> dict:
    out = {"code": code, "message": message, "request_id": request_id(request)}
    if details:
        out["details"] = details
    return out


def install(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(request: Request, e: ApiError):
        return JSONResponse(body(request, e.code, e.message, e.details), e.status, headers=e.headers)

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, e: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in err["loc"] if p != "body"), "problem": err["msg"]}
                   for err in e.errors()]
        return JSONResponse(body(request, "validation_error", "The request is not valid.", details), 422)

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, e: StarletteHTTPException):
        if e.status_code == 404:
            return JSONResponse(body(request, "not_found", "Not found."), 404)
        if e.status_code == 405:
            return JSONResponse(body(request, "method_not_allowed", "This method is not allowed here."), 405)
        return JSONResponse(body(request, "http_error", str(e.detail)), e.status_code)

    @app.exception_handler(DatabaseUnavailable)
    async def database(request: Request, e: DatabaseUnavailable):
        logger.error("database unavailable: %s (request %s)", e, request_id(request))
        return JSONResponse(body(request, "database_unavailable", "The database is not available. Try again soon."),
                            503, headers={"Retry-After": "5"})

    @app.exception_handler(Exception)
    async def unexpected(request: Request, e: Exception):
        logger.exception("unexpected error (request %s)", request_id(request))
        return JSONResponse(body(request, "internal_error", "Something went wrong on our side."), 500)
