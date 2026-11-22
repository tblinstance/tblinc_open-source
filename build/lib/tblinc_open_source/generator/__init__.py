"""Modular project generator package for `tblinc create ai <name>`."""

from .builder import create_ai_project, sanitize_project_name

__all__ = ["create_ai_project", "sanitize_project_name"]
