"""HTTP Request, Response, Cookie, and Error primitives for the tblinc web framework."""

from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.cookies import SimpleCookie
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs


class HttpError(Exception):
    """Base HTTP exception mapped cleanly to HTTP responses by TblincApp."""

    def __init__(self, status: int = 500, message: str = "Internal Server Error") -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class Http400(HttpError):
    def __init__(self, message: str = "Bad Request") -> None:
        super().__init__(400, message)


class Http403(HttpError):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(403, message)


class Http404(HttpError):
    def __init__(self, message: str = "Not Found") -> None:
        super().__init__(404, message)


class Http429(HttpError):
    def __init__(self, message: str = "Too Many Requests — Token or Request Quota Exceeded") -> None:
        super().__init__(429, message)


class Request:
    """High-level HTTP request constructed from a WSGI environ dictionary."""

    def __init__(self, environ: dict[str, Any], app: Any = None) -> None:
        self.environ = environ
        self.app = app
        self.method: str = environ.get("REQUEST_METHOD", "GET").upper()
        self.path: str = environ.get("PATH_INFO", "/") or "/"
        self.query_string: str = environ.get("QUERY_STRING", "")
        self.scheme: str = environ.get("wsgi.url_scheme", "http")
        self.host: str = environ.get("HTTP_HOST") or environ.get("SERVER_NAME", "localhost")
        self.remote_addr: str = environ.get("REMOTE_ADDR", "127.0.0.1")

        # Parse headers
        self.headers: dict[str, str] = {}
        for key, val in environ.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").title()
                self.headers[header_name] = str(val)
        if "CONTENT_TYPE" in environ:
            self.headers["Content-Type"] = str(environ["CONTENT_TYPE"])
        if "CONTENT_LENGTH" in environ and environ["CONTENT_LENGTH"]:
            self.headers["Content-Length"] = str(environ["CONTENT_LENGTH"])

        # Parse query params (keep single values convenient + multi-value accessible)
        raw_qs = parse_qs(self.query_string, keep_blank_values=True)
        self.query_multi: dict[str, list[str]] = raw_qs
        self.GET: dict[str, str] = {k: v[-1] if v else "" for k, v in raw_qs.items()}

        # Parse cookies
        self.cookies: dict[str, str] = {}
        cookie_hdr = environ.get("HTTP_COOKIE", "")
        if cookie_hdr:
            jar = SimpleCookie()
            jar.load(cookie_hdr)
            for k, morsel in jar.items():
                self.cookies[k] = morsel.value

        # Read raw body
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or 0)
        except ValueError:
            content_length = 0
        wsgi_input = environ.get("wsgi.input")
        self.body: bytes = wsgi_input.read(content_length) if (wsgi_input and content_length > 0) else b""

        # Parse POST form & JSON bodies lazily/cleanly
        self.POST: dict[str, str] = {}
        self.POST_multi: dict[str, list[str]] = {}
        self._json_cache: Any = None
        self._json_loaded: bool = False

        ctype = self.content_type
        if self.body and "application/x-www-form-urlencoded" in ctype:
            parsed = parse_qs(self.body.decode("utf-8", errors="replace"), keep_blank_values=True)
            self.POST_multi = parsed
            self.POST = {k: v[-1] if v else "" for k, v in parsed.items()}

        # Mutable attributes populated by router and middleware
        self.path_params: dict[str, Any] = {}
        self.session: dict[str, Any] = {}
        self.session_key: str | None = None
        self.user: Any = None
        self.csrf_token: str = ""
        self.messages: list[dict[str, str]] = []

    @property
    def content_type(self) -> str:
        return self.headers.get("Content-Type", "").lower()

    @property
    def full_path(self) -> str:
        return f"{self.path}?{self.query_string}" if self.query_string else self.path

    @property
    def is_json(self) -> bool:
        return "application/json" in self.content_type

    def json(self) -> Any:
        """Decode and cache JSON request body."""
        if not self._json_loaded:
            self._json_loaded = True
            if not self.body:
                self._json_cache = {}
            else:
                try:
                    self._json_cache = json.loads(self.body.decode("utf-8"))
                except json.JSONDecodeError as exc:
                    raise Http400(f"Invalid JSON payload: {exc}") from exc
        return self._json_cache

    def header(self, name: str, default: str = "") -> str:
        target = name.lower()
        for k, v in self.headers.items():
            if k.lower() == target:
                return v
        return default


class Response:
    """HTTP response returned by views, controllers, and middleware."""

    def __init__(
        self,
        body: str | bytes = "",
        status: int = 200,
        content_type: str = "text/plain; charset=utf-8",
        headers: dict[str, str] | None = None,
    ) -> None:
        self.body: bytes = body.encode("utf-8") if isinstance(body, str) else bytes(body)
        self.status: int = int(status)
        self.headers: list[tuple[str, str]] = [("Content-Type", content_type)]
        if headers:
            for k, v in headers.items():
                self.set_header(k, v)
        self._cookies = SimpleCookie()

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    @property
    def status_line(self) -> str:
        try:
            phrase = HTTPStatus(self.status).phrase
        except ValueError:
            phrase = "Unknown"
        return f"{self.status} {phrase}"

    def set_header(self, name: str, value: str) -> None:
        lower = name.lower()
        self.headers = [(k, v) for k, v in self.headers if k.lower() != lower]
        self.headers.append((name, value))

    def get_header(self, name: str, default: str = "") -> str:
        lower = name.lower()
        for k, v in self.headers:
            if k.lower() == lower:
                return v
        return default

    def set_cookie(
        self,
        name: str,
        value: str,
        *,
        max_age: int | None = None,
        path: str = "/",
        httponly: bool = True,
        samesite: str = "Lax",
        secure: bool = False,
    ) -> None:
        self._cookies[name] = value
        morsel = self._cookies[name]
        morsel["path"] = path
        if max_age is not None:
            morsel["max-age"] = str(max_age)
        if httponly:
            morsel["httponly"] = True
        if samesite:
            morsel["samesite"] = samesite
        if secure:
            morsel["secure"] = True

    def delete_cookie(self, name: str, path: str = "/") -> None:
        self.set_cookie(name, "", max_age=0, path=path)

    def wsgi_headers(self) -> list[tuple[str, str]]:
        hdrs = list(self.headers)
        if not any(k.lower() == "content-length" for k, _ in hdrs):
            hdrs.append(("Content-Length", str(len(self.body))))
        for morsel in self._cookies.values():
            hdrs.append(("Set-Cookie", morsel.OutputString()))
        return hdrs


class HtmlResponse(Response):
    def __init__(self, html: str, status: int = 200, headers: dict[str, str] | None = None) -> None:
        super().__init__(html, status=status, content_type="text/html; charset=utf-8", headers=headers)


class JsonResponse(Response):
    def __init__(self, data: Any, status: int = 200, headers: dict[str, str] | None = None) -> None:
        payload = json.dumps(data, default=str)
        super().__init__(payload, status=status, content_type="application/json; charset=utf-8", headers=headers)


class RedirectResponse(Response):
    def __init__(self, location: str, status: int = 302) -> None:
        super().__init__("", status=status, content_type="text/plain; charset=utf-8", headers={"Location": location})


class StaticResponse(Response):
    def __init__(self, file_path: Path) -> None:
        ctype, _ = mimetypes.guess_type(str(file_path))
        super().__init__(
            file_path.read_bytes(),
            status=200,
            content_type=ctype or "application/octet-stream",
            headers={"Cache-Control": "no-cache, must-revalidate"},
        )
