"""Argument parser and entrypoint for the `tblinc` command-line interface."""

from __future__ import annotations

import argparse
from typing import Sequence

from .commands import (
    cmd_create,
    cmd_createsuperuser,
    cmd_devices,
    cmd_info,
    cmd_install,
    cmd_migrate,
    cmd_models,
    cmd_serve,
    cmd_verify,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tblinc",
        description="tblinc — High-level Python AI & MTV/MVC Web Framework (no Django/Flask/FastAPI).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create_p = sub.add_parser("create", help="Scaffold a new tblinc AI web project (`tblinc create ai <name>`)")
    create_p.add_argument("kind", help="Use 'ai' followed by project name, or pass project name directly")
    create_p.add_argument("name", nargs="?", default=None, help="Name of the new AI project")
    create_p.add_argument("--dir", default=None, help="Parent directory where the project folder will be created")
    create_p.set_defaults(func=cmd_create)

    serve_p = sub.add_parser("serve", aliases=["run"], help="Start the tblinc web server for a project")
    serve_p.add_argument("project_dir", nargs="?", default=".", help="Path to the tblinc project directory")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.set_defaults(func=cmd_serve)

    mig_p = sub.add_parser("migrate", help="Create database tables for all ORM models in a project")
    mig_p.add_argument("project_dir", nargs="?", default=".", help="Path to the tblinc project directory")
    mig_p.set_defaults(func=cmd_migrate)

    su_p = sub.add_parser("createsuperuser", help="Create or update a staff superuser for the Admin Panel")
    su_p.add_argument("project_dir", nargs="?", default=".", help="Path to the tblinc project directory")
    su_p.add_argument("--username", default=None, help="Superuser username (prompts if omitted)")
    su_p.add_argument("--password", default=None, help="Superuser password (prompts if omitted)")
    su_p.add_argument("--email", default="", help="Superuser email address")
    su_p.set_defaults(func=cmd_createsuperuser)

    models_p = sub.add_parser("models", help="Inspect or run the 25 built-in AI models")
    models_p.add_argument(
        "models_cmd",
        nargs="?",
        default="list",
        help="Action ('list', 'demo', 'run') or a model key directly (e.g. 'multimodal', 'chat')",
    )
    models_p.add_argument(
        "key",
        nargs="?",
        default=None,
        help="Model key when using 'demo'/'run' (e.g. chat, multimodal, image, search, vision)",
    )
    models_p.add_argument("--input", default=None, help="Optional JSON input payload")
    models_p.set_defaults(func=cmd_models)

    ver_p = sub.add_parser("verify", help="Verify all 25 built-in AI models (train, predict, save/load)")
    ver_p.add_argument("--json", action="store_true", help="Output verification report as JSON")
    ver_p.set_defaults(func=cmd_verify)

    dev_p = sub.add_parser("devices", help="Detect CUDA, Intel XPU, OpenVINO, CPU, and installed ML backends")
    dev_p.set_defaults(func=cmd_devices)

    info_p = sub.add_parser("info", help="Show framework, compute, and AI model catalog information")
    info_p.set_defaults(func=cmd_info)

    inst_p = sub.add_parser("install", help="Install optional AI/ML package stacks from pyproject.toml (`tblinc install [stack ...]`)")
    inst_p.add_argument("stacks", nargs="*", default=[], help="AI stack names (e.g. torch, llm, vision, tabular, rag, ai-clients, all)")
    inst_p.add_argument("--list", dest="list_only", action="store_true", help="List available AI package stacks")
    inst_p.add_argument("--dry-run", action="store_true", help="Print the pip install command without executing")
    inst_p.set_defaults(func=cmd_install)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))
