from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, is_production: bool) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self._is_production = is_production

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response: Response = await call_next(request)
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
        if self._is_production:
            headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        if "server" in headers:
            del headers["server"]
        return response
