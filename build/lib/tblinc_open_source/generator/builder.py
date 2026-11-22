"""Modular project builder powering `tblinc create ai <name>`."""

from __future__ import annotations

import re
import secrets
from pathlib import Path

from .backend_files import build_backend_files
from .html_templates import build_html_templates
from .theme_assets import build_theme_assets


def sanitize_project_name(name: str) -> str:
    """Normalize a user-provided project name into a clean filesystem slug."""
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip()).strip("_-")
    if not cleaned:
        raise ValueError("Project name must contain at least one alphanumeric character.")
    return cleaned


_ACRONYMS = {"ai", "ml", "llm", "rag", "vlm", "nlp", "api", "tts", "asr", "cart", "ddpm", "knn", "mlp"}


def _format_project_title(slug: str) -> str:
    """Format a project slug into a crisp human-readable app title without duplicate AI wording."""
    if slug.lower() in {"ai", "tblinc", "tblinc_ai", "tblinc-ai"}:
        return "tblinc AI"
    words: list[str] = []
    for part in re.split(r"[_-]+", slug):
        low = part.lower()
        if not low:
            continue
        if low == "tblinc":
            words.append("tblinc")
        elif low in _ACRONYMS:
            words.append(low.upper())
        else:
            words.append(part.title())
    return " ".join(words) or "tblinc AI"


def _safe_cwd() -> Path:
    import os

    try:
        return Path.cwd().resolve()
    except FileNotFoundError:
        pwd_env = os.environ.get("PWD")
        if pwd_env:
            p = Path(pwd_env)
            p.mkdir(parents=True, exist_ok=True)
            try:
                os.chdir(str(p))
            except OSError:
                pass
            return p.resolve()
        return Path.home().resolve()


def create_ai_project(
    name: str = "ai",
    destination: str | Path | None = None,
    *,
    overwrite: bool = True,
) -> Path:
    """Generate or update a full-folder MTV/MVC AI web app with 100% Light/Dark & PC/Tablet/Mobile UI."""
    raw_name = (name or "").strip() or "ai"
    cwd = _safe_cwd()
    if raw_name in {".", "./"}:
        slug = sanitize_project_name(cwd.name or "ai")
        root = Path(destination).resolve() if destination is not None else cwd
    else:
        slug = sanitize_project_name(raw_name)
        if destination is not None:
            root = Path(destination).resolve() / slug
        elif cwd.name.lower() == slug.lower() and ((cwd / "app.py").exists() or (cwd / "templates").exists()):
            # Running `tblinc create ai ai` while already inside `~/ai` updates `~/ai` in place
            root = cwd
        else:
            root = cwd / slug

    if root.exists() and not overwrite and any(root.iterdir()):
        raise FileExistsError(f"Target directory already exists and is not empty: {root}")

    title = _format_project_title(slug)
    secret = secrets.token_hex(32)
    existing_settings = root / "config" / "settings.py"
    if existing_settings.is_file():
        try:
            m = re.search(r'SECRET_KEY\s*=\s*"([^"]+)"', existing_settings.read_text(encoding="utf-8"))
            if m:
                secret = m.group(1)
        except Exception:
            pass

    manifest: dict[str, str] = {
        **build_backend_files(slug=slug, title=title, secret=secret),
        **build_theme_assets(),
        **build_html_templates(),
    }

    for rel_path, content in manifest.items():
        target = root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return root
