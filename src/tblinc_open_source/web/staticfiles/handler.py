"""Safe static asset handler with directory-traversal protection and MIME typing."""

from __future__ import annotations

from pathlib import Path

from ..http import Response, StaticResponse


class StaticFileHandler:
    """Serves static files from a configured root directory with path-traversal protection."""

    def __init__(self, static_dir: str | Path | None, url_prefix: str = "/static/") -> None:
        self.static_dir: Path | None = Path(static_dir) if static_dir else None
        self.url_prefix: str = "/" + url_prefix.strip("/") + "/"

    def serve(self, req_path: str) -> Response | None:
        if not self.static_dir or not req_path.startswith(self.url_prefix):
            return None
        rel = req_path[len(self.url_prefix) :].lstrip("/")
        if not rel:
            return None
        root = self.static_dir.resolve()
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        if candidate.is_file():
            return StaticResponse(candidate)
        return None
