"""Hardware accelerator and optional ML backend detection."""

from .runtime import detect_hardware, installed_backends, select_device, system_report

__all__ = ["detect_hardware", "installed_backends", "select_device", "system_report"]
