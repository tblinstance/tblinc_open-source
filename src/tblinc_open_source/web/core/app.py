"""TblincApp core WSGI application and threaded development server."""

from __future__ import annotations

import secrets
from pathlib import Path
from socketserver import ThreadingMixIn
from typing import Any, Callable, Iterable
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from ..admin import AdminSite
from ..auth import register_auth_routes
from ..http import HtmlResponse, Http404, HttpError, JsonResponse, Request, Response
from ..middleware import security_headers_middleware, session_and_auth_middleware, timing_middleware
from ..orm import Database, default_db
from ..routing import Router
from ..staticfiles import StaticFileHandler
from ..templates import TemplateEngine, register_builtin_templates
from ..testing import TestClient


class _ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = True


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        print(f"[tblinc] {self.address_string()} - {format % args}")


class TblincApp:
    """High-level standalone MTV/MVC Python Web Application with ORM, Auth, Templates, and Auto-Admin."""

    def __init__(
        self,
        *,
        title: str = "tblinc AI",
        database_path: str | Path = ":memory:",
        template_dirs: list[str | Path] | None = None,
        static_dir: str | Path | None = None,
        secret_key: str | None = None,
        debug: bool = True,
        enable_admin: bool = True,
        enable_auth: bool = True,
        admin_prefix: str = "/admin",
    ) -> None:
        cleaned_title = (title or "").strip()
        if cleaned_title.lower() in {"", "ai", "tblinc", "tblinc ai", "tblinc_ai", "tblinc-ai"}:
            cleaned_title = "tblinc AI"
        self.title = cleaned_title
        self.debug = debug
        self.secret_key = secret_key or secrets.token_hex(32)
        self.csrf_exempt_prefixes: tuple[str, ...] = ("/api/",)
        self.static_dir = Path(static_dir) if static_dir else None
        self.static_handler = StaticFileHandler(static_dir)

        self.db: Database = default_db
        self.db.configure(database_path)

        self._auto_sync_project_assets(template_dirs, static_dir)
        self.router = Router()
        self.templates = TemplateEngine(template_dirs or [])
        register_builtin_templates(self.templates)

        self.middlewares: list[Callable[[Request, Callable[[Request], Response]], Response]] = [
            timing_middleware,
            security_headers_middleware,
            session_and_auth_middleware,
        ]
        self.admin = AdminSite(title=f"{self.title} Admin", prefix=admin_prefix)
        self._admin_mounted = False
        self._enable_admin = enable_admin

        if enable_auth:
            register_auth_routes(self)
        if enable_admin:
            self.mount_admin()

    def _auto_sync_project_assets(
        self,
        template_dirs: list[str | Path] | None,
        static_dir: str | Path | None,
    ) -> None:
        """Keep scaffolded project templates/ and static/ assets in sync with the latest framework templates."""
        try:
            from ...generator.html_templates import build_html_templates
            from ...generator.theme_assets import build_theme_assets

            if template_dirs:
                t_root = Path(template_dirs[0]).resolve()
                if t_root.name == "templates" and (t_root / "layouts" / "base.html").exists():
                    proj_root = t_root.parent
                    for rel_path, content in build_html_templates().items():
                        dest = proj_root / rel_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(content, encoding="utf-8")
            if static_dir:
                s_root = Path(static_dir).resolve()
                if s_root.name == "static" and s_root.exists():
                    proj_root = s_root.parent
                    for rel_path, content in build_theme_assets().items():
                        dest = proj_root / rel_path
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(content, encoding="utf-8")
        except Exception:
            pass

    def mount_admin(self) -> None:
        if not self._admin_mounted:
            self.admin.mount(self)
            self._admin_mounted = True

    def migrate(self) -> list[str]:
        """Auto-create SQLite tables for all registered ORM models."""
        return self.db.migrate()

    def use(self, middleware: Callable[[Request, Callable[[Request], Response]], Response]) -> None:
        self.middlewares.append(middleware)

    def route(
        self,
        pattern: str,
        *,
        methods: tuple[str, ...] | list[str] = ("GET",),
        name: str | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.route(pattern, methods=methods, name=name)

    def get(self, pattern: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.get(pattern, name=name)

    def post(self, pattern: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.router.post(pattern, name=name)

    def add_route(
        self,
        pattern: str,
        handler: Callable[..., Any],
        *,
        methods: tuple[str, ...] | list[str] = ("GET", "POST"),
        name: str | None = None,
    ) -> None:
        self.router.add(pattern, handler, methods=methods, name=name)

    def include_routes(self, routes: list[tuple[str, Callable[..., Any], tuple[str, ...], str | None]]) -> None:
        for pattern, handler, methods, name in routes:
            self.router.add(pattern, handler, methods=methods, name=name)

    def url_for(self, name: str, **params: Any) -> str:
        return self.router.url_for(name, **params)

    def render(
        self,
        request: Request,
        template_name: str,
        context: dict[str, Any] | None = None,
        status: int = 200,
    ) -> HtmlResponse:
        merged = {
            "site_title": self.title,
            "request": request,
            "user": request.user,
            "csrf_token": request.csrf_token,
            **(context or {}),
        }
        rendered = self.templates.render(template_name, merged)
        return HtmlResponse(rendered, status=status)

    def _coerce_response(self, result: Any) -> Response:
        if isinstance(result, Response):
            return result
        if isinstance(result, (dict, list)):
            return JsonResponse(result)
        return HtmlResponse(str(result))

    def _dispatch(self, request: Request) -> Response:
        static_resp = self.static_handler.serve(request.path)
        if static_resp is not None:
            return static_resp
        resolved = self.router.resolve(request.path, request.method)
        if resolved is None:
            raise Http404(f"No route matched '{request.path}'")
        route, params = resolved
        request.path_params = params
        return self._coerce_response(route.handler(request, **params))

    def handle_request(self, request: Request) -> Response:
        def invoke(idx: int, req: Request) -> Response:
            if idx < len(self.middlewares):
                return self.middlewares[idx](req, lambda r: invoke(idx + 1, r))
            return self._dispatch(req)

        try:
            return invoke(0, request)
        except HttpError as exc:
            if request.path.startswith("/api/") or request.is_json:
                return JsonResponse({"error": exc.message, "status": exc.status}, status=exc.status)
            return self.render(
                request,
                "tblinc_error.html",
                {"status": exc.status, "title": "Error", "message": exc.message},
                status=exc.status,
            )
        except Exception as exc:  # pragma: no cover - safety net
            msg = f"{type(exc).__name__}: {exc}" if self.debug else "Internal Server Error"
            if request.path.startswith("/api/") or request.is_json:
                return JsonResponse({"error": msg, "status": 500}, status=500)
            return self.render(
                request,
                "tblinc_error.html",
                {"status": 500, "title": "Server Error", "message": msg},
                status=500,
            )

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        request = Request(environ, app=self)
        response = self.handle_request(request)
        start_response(response.status_line, response.wsgi_headers())
        return [response.body]

    def test_client(self) -> TestClient:
        return TestClient(self)

    def run(self, host: str = "127.0.0.1", port: int = 8000) -> None:
        """Start the built-in threaded WSGI development server."""
        self.migrate()
        server = make_server(host, port, self, server_class=_ThreadedWSGIServer, handler_class=_QuietHandler)
        print(f"tblinc server running at http://{host}:{port}/")
        print(f"Admin panel available at http://{host}:{port}{self.admin.prefix}/")
        print(f"tblinc AI (ai_chat) at   http://{host}:{port}{self.admin.prefix}/ai/")
        print(f"SQLite database at       {self.db.path}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down tblinc server.")
        finally:
            server.server_close()
