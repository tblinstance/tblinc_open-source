"""SQLite-backed Admin Settings store for tblinc AI platform configuration."""

from __future__ import annotations

from typing import Any

from ..orm import CharField, DateTimeField, DoesNotExist, Model
from .quota import ModelQuota, ensure_default_quotas

DEFAULT_SETTINGS: dict[str, str] = {
    "site_title": "tblinc AI",
    "default_theme": "system",
    "default_sidenav": "expanded",
    "default_ai_model": "chat",
    "default_device": "auto",
    "require_studio_api_key": "false",
    "allow_registration": "true",
}


class AppSetting(Model):
    """Key-value configuration persisted in SQLite and managed from /admin/settings/."""

    key = CharField(max_length=80, unique=True)
    value = CharField(max_length=255, blank=True, default="")
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        table_name = "tblinc_settings"
        verbose_name = "Setting"
        verbose_name_plural = "Settings"


def get_app_settings(app: Any = None) -> dict[str, Any]:
    """Return merged platform settings + global quota limits."""
    ensure_default_quotas()
    result: dict[str, Any] = dict(DEFAULT_SETTINGS)
    if app is not None and getattr(app, "title", None):
        result["site_title"] = app.title
    try:
        for row in AppSetting.objects.all():
            result[row.key] = row.value
    except Exception:
        pass

    result["require_studio_api_key_bool"] = str(result.get("require_studio_api_key", "false")).lower() == "true"
    result["allow_registration_bool"] = str(result.get("allow_registration", "true")).lower() == "true"

    try:
        gq = ModelQuota.objects.get(model_key="*")
        result["global_token_limit"] = int(gq.token_limit or 0)
        result["global_request_limit"] = int(gq.request_limit or 0)
    except (DoesNotExist, Exception):
        result["global_token_limit"] = 500_000
        result["global_request_limit"] = 5_000
    return result


def update_app_settings(payload: dict[str, Any], app: Any = None) -> dict[str, Any]:
    """Persist updated Admin Settings into SQLite and apply live runtime updates."""
    for key in DEFAULT_SETTINGS:
        if key not in payload:
            continue
        raw = payload[key]
        val = ("true" if raw else "false") if isinstance(raw, bool) else str(raw).strip()
        try:
            row = AppSetting.objects.get(key=key)
            row.value = val
            row.save()
        except DoesNotExist:
            AppSetting.objects.create(key=key, value=val)

    # Sync live app title & admin title when updated
    new_title = str(payload.get("site_title", "")).strip()
    if app is not None and new_title:
        app.title = new_title
        if hasattr(app, "admin") and app.admin is not None:
            app.admin.title = f"{new_title} Admin"

    # Optionally sync global '*' quota limits right from Settings
    if "global_token_limit" in payload or "global_request_limit" in payload:
        ensure_default_quotas()
        try:
            gq = ModelQuota.objects.get(model_key="*")
            if "global_token_limit" in payload:
                gq.token_limit = max(0, int(payload["global_token_limit"]))
            if "global_request_limit" in payload:
                gq.request_limit = max(0, int(payload["global_request_limit"]))
            gq.save()
        except (DoesNotExist, ValueError, TypeError):
            pass

    return get_app_settings(app=app)
