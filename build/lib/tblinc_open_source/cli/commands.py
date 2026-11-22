"""Command handlers for the `tblinc` CLI."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

from ..ai_models import detect_hardware, list_models, registry, run_demo, system_report, verify_all_models
from ..generator import create_ai_project
from ..web import create_superuser, default_db


def _safe_resolve_dir(raw_dir: str | Path | None = None) -> Path:
    """Resolve a directory safely even if the shell CWD inode was recreated."""
    try:
        if raw_dir is None or str(raw_dir).strip() in {"", "."}:
            return Path.cwd().resolve()
        return Path(raw_dir).resolve()
    except FileNotFoundError:
        pwd_env = os.environ.get("PWD")
        if pwd_env and Path(pwd_env).exists():
            resolved = Path(pwd_env).resolve()
            try:
                os.chdir(str(resolved))
            except OSError:
                pass
            if raw_dir and str(raw_dir).strip() not in {"", "."}:
                return (resolved / str(raw_dir)).resolve()
            return resolved
        return Path.home().resolve()


def load_project_app(project_dir: str | Path) -> Any:
    """Dynamically load a scaffolded tblinc project's `app.py` entrypoint."""
    proj_dir = _safe_resolve_dir(project_dir)
    app_file = proj_dir / "app.py"
    if not app_file.is_file():
        # Check if a single child project folder has app.py (e.g. ./ai/app.py)
        candidates = [p for p in proj_dir.glob("*/app.py") if p.is_file()] if proj_dir.is_dir() else []
        if len(candidates) == 1:
            app_file = candidates[0]
            proj_dir = app_file.parent
        else:
            raise FileNotFoundError(
                f"Could not find app.py in {proj_dir}. Run `tblinc create ai` first or pass the project path."
            )
    try:
        os.chdir(str(proj_dir))
    except OSError:
        pass
    if str(proj_dir) not in sys.path:
        sys.path.insert(0, str(proj_dir))
    spec = importlib.util.spec_from_file_location("tblinc_user_app", app_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {app_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, "application", None) or module.create_app()


def cmd_create(args: argparse.Namespace) -> int:
    cwd = _safe_resolve_dir(".")
    if args.kind == "ai":
        if not args.name:
            project_name = "." if ((cwd / "app.py").exists() or cwd.name.lower() == "ai") else "ai"
        else:
            project_name = args.name
    else:
        project_name = args.kind

    target = create_ai_project(project_name, destination=args.dir, overwrite=True)
    print(f"Created/updated tblinc AI web project at: {target}")
    print("\nNext steps:")
    if target.resolve() != cwd:
        print(f"  cd {target.name}")
    print("  tblinc createsuperuser")
    print("  tblinc serve")
    print("\nAdmin Panel:")
    print("  URL:      http://127.0.0.1:8000/admin/")
    print("  AI Chat:  http://127.0.0.1:8000/admin/ai/")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    try:
        application = load_project_app(args.project_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    application.run(host=args.host, port=args.port)
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    try:
        application = load_project_app(args.project_dir)
        tables = application.migrate()
    except FileNotFoundError:
        proj_dir = _safe_resolve_dir(args.project_dir)
        db_path = proj_dir / "db.sqlite3"
        default_db.configure(db_path)
        tables = default_db.migrate()
    print("Migrated tables:", ", ".join(tables))
    return 0


def cmd_createsuperuser(args: argparse.Namespace) -> int:
    import getpass

    try:
        load_project_app(args.project_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    username = (args.username or "").strip() or input("Username: ").strip()
    email = (args.email or "").strip()
    if not args.username and not email:
        email = input("Email (optional): ").strip()
    password = args.password or getpass.getpass("Password: ")
    if not username or not password:
        print("Error: username and password are required.", file=sys.stderr)
        return 1
    user = create_superuser(username, password, email=email)
    print(f"Configured superuser '{user.username}' (id={user.pk}).")
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    cmd = (getattr(args, "models_cmd", None) or "list").strip().lower()
    target_key = (getattr(args, "key", None) or "").strip().lower()

    if not target_key and (cmd in {"list", "ls", "all", "show"} or cmd.startswith("list")):
        models = list_models()
        print(f"tblinc built-in AI models ({len(models)} model folders):\n")
        for idx, m in enumerate(models, start=1):
            print(f"  {idx:2d}. {m['key']:20s} | {m['category']:22s} | {m['name']} — {m['task']}")
        return 0

    model_to_run = target_key or cmd
    try:
        resolved = registry.resolve_key(model_to_run)
        custom = json.loads(args.input) if getattr(args, "input", None) else None
        output = run_demo(resolved, custom_input=custom)
        print(json.dumps(output, indent=2, default=str))
        return 0
    except KeyError:
        valid = ", ".join(registry.keys())
        print(
            f"Error: Unknown AI model '{model_to_run}'. Choose one of: {valid}\n"
            "Or run `tblinc models list` to view all 25 models.",
            file=sys.stderr,
        )
        return 2


def cmd_verify(args: argparse.Namespace) -> int:
    report = verify_all_models()
    hw = detect_hardware()
    if args.json:
        print(json.dumps({"hardware": hw, "models": report}, indent=2, default=str))
    else:
        print(f"Hardware: preferred={hw['preferred_device']} | cpu_cores={hw['cpu_cores']} | python={hw['python_version']}")
        print(f"AI Model Verification ({report['passed']}/{report['total']} passed):\n")
        for item in report["results"]:
            status = "PASS" if item["ok"] else "FAIL"
            extra = f"latency={item['latency_ms']}ms" if item["ok"] else f"error={item.get('error')}"
            print(f"  [{status}] {item['key']:20s} | {item['category']:22s} | {item['name']} ({extra})")
    return 0 if report["all_ok"] else 1


def cmd_devices(_: argparse.Namespace) -> int:
    print(json.dumps(system_report(), indent=2))
    return 0


def cmd_info(_: argparse.Namespace) -> int:
    from .. import __version__

    models = list_models()
    hw = detect_hardware()
    print(f"tblinc v{__version__}")
    print("Web Framework: 12-module Standalone Python MTV/MVC (ORM, Templates, Forms, Auth, Auto-Admin)")
    print("UI Stack CDN:  Tailwind CSS + Lucide Icons + Motion (Light/Dark · PC/Tablet/Mobile)")
    print(f"AI Models:     {len(models)} modular model folders ready (zero external core deps)")
    print(
        f"Compute:       preferred={hw['preferred_device']} "
        f"(CPU cores: {hw['cpu_cores']}, CUDA: {hw['cuda']['available']}, XPU: {hw['xpu']['available']})"
    )
    print("Server CLI:    tblinc serve [--host 127.0.0.1] [--port 8000]")
    return 0


_AI_STACKS: dict[str, list[str]] = {
    "torch": ["torch>=2.4", "torchvision>=0.19", "torchaudio>=2.4", "safetensors>=0.4", "onnx>=1.16"],
    "tensorflow": ["tensorflow>=2.18.0rc0", "tensorflow[and-cuda]>=2.18.0rc0", "keras>=3.5"],
    "jax": ["jax>=0.4.35", "keras>=3.5"],
    "llm": [
        "transformers>=4.46",
        "diffusers>=0.31",
        "accelerate>=1.0",
        "peft>=0.13",
        "trl>=0.12",
        "datasets>=3.0",
        "tokenizers>=0.20",
        "huggingface-hub>=0.26",
        "sentencepiece>=0.2",
        "sentence-transformers>=3.2",
    ],
    "vision": ["ultralytics>=8.3", "timm>=1.0", "opencv-python>=4.10", "pillow>=10.4"],
    "video": ["opencv-python>=4.10"],
    "audio": ["librosa>=0.10", "soundfile>=0.12"],
    "tts": ["coqui-tts>=0.25"],
    "tabular": [
        "numpy>=1.26",
        "scipy>=1.14",
        "pandas>=2.2",
        "scikit-learn>=1.5",
        "xgboost>=2.1",
        "lightgbm>=4.5",
    ],
    "rag": [
        "langchain>=0.3",
        "qdrant-client>=1.12",
        "tiktoken>=0.8",
    ],
    "ai-clients": ["openai>=1.52", "anthropic>=0.37", "google-genai>=1.0", "litellm>=1.50"],
    "cuda": ["tensorflow[and-cuda]>=2.18.0rc0", "jax[cuda12]>=0.4.35", "bitsandbytes>=0.44", "onnxruntime-gpu>=1.19"],
    "xpu": ["optimum-intel>=1.20", "openvino>=2024.4"],
}


def cmd_install(args: argparse.Namespace) -> int:
    import shutil
    import subprocess

    stacks = [s.strip().lower() for s in (getattr(args, "stacks", None) or []) if s.strip()]
    if getattr(args, "list_only", False) or not stacks:
        print("Available tblinc AI optional package stacks (defined in pyproject.toml):\n")
        for name, pkgs in _AI_STACKS.items():
            print(f"  - {name:12s}: {', '.join(pkgs)}")
        print("\nInstall commands:")
        print("  tblinc install tensorflow cuda")
        print("  tblinc install torch llm vision")
        print("  tblinc install all")
        return 0

    selected: list[str] = []
    for st in stacks:
        if st == "all":
            for group_name, pkgs in _AI_STACKS.items():
                if group_name not in {"xpu", "tts"}:
                    for p in pkgs:
                        if p not in selected:
                            selected.append(p)
        elif st in _AI_STACKS:
            for p in _AI_STACKS[st]:
                if p not in selected:
                    selected.append(p)
        else:
            selected.append(st)

    # Use disk-backed TMPDIR inside ~/.cache/tblinc_pip_tmp instead of small RAM-limited /tmp tmpfs
    pip_tmp = Path.home() / ".cache" / "tblinc_pip_tmp"
    base_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--user",
        "--break-system-packages",
        "--no-cache-dir",
        "--pre",
    ]
    if getattr(args, "dry_run", False):
        print(f"TMPDIR={pip_tmp} " + " ".join([*base_cmd, *selected]))
        return 0

    pip_tmp.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["TMPDIR"] = str(pip_tmp)
    env["TEMP"] = str(pip_tmp)
    env["TMP"] = str(pip_tmp)

    print(f"Installing {len(selected)} AI packages (using disk TMPDIR={pip_tmp}): {', '.join(selected)}")
    installed: list[str] = []
    skipped: list[str] = []
    try:
        for idx, pkg in enumerate(selected, start=1):
            print(f"\n[{idx}/{len(selected)}] Installing {pkg} ...")
            rc = subprocess.call([*base_cmd, pkg], env=env)
            # Clean unpacked wheel temp files after each package to prevent Errno 28 (No space left)
            for child in pip_tmp.iterdir():
                shutil.rmtree(child, ignore_errors=True)
            if rc == 0:
                installed.append(pkg)
            else:
                skipped.append(pkg)
    finally:
        shutil.rmtree(pip_tmp, ignore_errors=True)

    print(f"\nInstalled ({len(installed)}/{len(selected)}): {', '.join(installed) or 'none'}")
    if skipped:
        print(f"Skipped ({len(skipped)}): {', '.join(skipped)}")
    return 0 if installed else 1
