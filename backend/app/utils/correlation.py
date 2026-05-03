import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

CORRELATION_ID_HEADER = "X-Correlation-ID"
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="-")


def get_correlation_id() -> str:
    return correlation_id_var.get()


def set_correlation_id(value: str) -> None:
    correlation_id_var.set(value)


def new_correlation_id() -> str:
    return uuid.uuid4().hex


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        cid = request.headers.get(CORRELATION_ID_HEADER) or new_correlation_id()
        token = correlation_id_var.set(cid)
        try:
            response: Response = await call_next(request)
            response.headers[CORRELATION_ID_HEADER] = cid
            return response
        finally:
            correlation_id_var.reset(token)
