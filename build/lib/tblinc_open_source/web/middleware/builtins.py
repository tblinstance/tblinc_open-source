"""Built-in middleware components: Session/Auth/CSRF, Security Headers, CORS, and Request Timing."""

from __future__ import annotations

import time
from typing import Callable

from ..auth import session_and_auth_middleware
from ..http import Request, Response

MiddlewareFn = Callable[[Request, Callable[[Request], Response]], Response]


def security_headers_middleware(request: Request, call_next: Callable[[Request], Response]) -> Response:
    """Attach baseline HTTP security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy)."""
    response = call_next(request)
    response.set_header("X-Content-Type-Options", "nosniff")
    response.set_header("X-Frame-Options", "SAMEORIGIN")
    response.set_header("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


def timing_middleware(request: Request, call_next: Callable[[Request], Response]) -> Response:
    """Measure server handling time and expose it via the X-Response-Time-Ms header."""
    t0 = time.perf_counter()
    response = call_next(request)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    response.set_header("X-Response-Time-Ms", f"{elapsed_ms:.2f}")
    return response


def make_cors_middleware(
    allow_origin: str = "*",
    allow_methods: str = "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    allow_headers: str = "Content-Type, Authorization, X-CSRF-Token",
) -> MiddlewareFn:
    """Create a configurable CORS middleware for API routes."""

    def cors_middleware(request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.method == "OPTIONS":
            resp = Response("", status=204)
        else:
            resp = call_next(request)
        resp.set_header("Access-Control-Allow-Origin", allow_origin)
        resp.set_header("Access-Control-Allow-Methods", allow_methods)
        resp.set_header("Access-Control-Allow-Headers", allow_headers)
        return resp

    return cors_middleware
