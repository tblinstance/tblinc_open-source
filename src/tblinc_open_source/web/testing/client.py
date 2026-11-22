"""In-process WSGI TestClient with cookie jar, form encoding, and JSON helpers."""

from __future__ import annotations

import io
import json
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import urlencode

from ..http import Response


class TestClient:
    """Zero-network WSGI test client for exercising tblinc apps, cookies, CSRF, and APIs."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.cookies: dict[str, str] = {}

    def request(
        self,
        method: str,
        path: str,
        *,
        data: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, str] | None = None,
    ) -> Response:
        if "?" in path:
            path_info, qs = path.split("?", 1)
        else:
            path_info, qs = path, ""

        body_bytes = b""
        content_type = ""
        if json_body is not None:
            body_bytes = json.dumps(json_body).encode("utf-8")
            content_type = "application/json"
        elif data is not None:
            body_bytes = urlencode(data).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"

        environ: dict[str, Any] = {
            "REQUEST_METHOD": method.upper(),
            "PATH_INFO": path_info,
            "QUERY_STRING": qs,
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "wsgi.url_scheme": "http",
            "wsgi.input": io.BytesIO(body_bytes),
            "CONTENT_LENGTH": str(len(body_bytes)),
        }
        if content_type:
            environ["CONTENT_TYPE"] = content_type
        if self.cookies:
            environ["HTTP_COOKIE"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        if headers:
            for k, v in headers.items():
                environ["HTTP_" + k.upper().replace("-", "_")] = v

        captured_status = "200 OK"
        captured_headers: list[tuple[str, str]] = []

        def start_response(status: str, resp_headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            nonlocal captured_status, captured_headers
            captured_status = status
            captured_headers = list(resp_headers)

        chunks = list(self.app(environ, start_response))
        raw_body = b"".join(chunks)
        code = int(captured_status.split(" ", 1)[0])
        ctype = "text/plain; charset=utf-8"
        extra: dict[str, str] = {}
        for k, v in captured_headers:
            if k.lower() == "content-type":
                ctype = v
            elif k.lower() == "set-cookie":
                jar = SimpleCookie()
                jar.load(v)
                for ck, morsel in jar.items():
                    if morsel["max-age"] == "0":
                        self.cookies.pop(ck, None)
                    else:
                        self.cookies[ck] = morsel.value
            else:
                extra[k] = v
        return Response(raw_body, status=code, content_type=ctype, headers=extra)

    def get(self, path: str, **kwargs: Any) -> Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Response:
        return self.request("PUT", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Response:
        return self.request("DELETE", path, **kwargs)
