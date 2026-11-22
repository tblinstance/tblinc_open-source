"""tblinc: High-level Python AI & Standalone MTV/MVC Web Framework."""

from . import ai_models, cli, generator, web
from .ai_models import (
    create_model,
    detect_hardware,
    list_models,
    registry,
    run_demo,
    select_device,
    system_report,
    verify_all_models,
)
from .generator import create_ai_project
from .web import AdminSite, Controller, Form, Model, ModelAdmin, ModelForm, TblincApp, path, render

__version__ = "0.1.0"

__all__ = [
    "AdminSite",
    "Controller",
    "Form",
    "Model",
    "ModelAdmin",
    "ModelForm",
    "TblincApp",
    "__version__",
    "ai_models",
    "cli",
    "create_ai_project",
    "create_model",
    "detect_hardware",
    "generator",
    "list_models",
    "path",
    "registry",
    "render",
    "run_demo",
    "select_device",
    "system_report",
    "verify_all_models",
    "web",
]
