"""Automatic Admin Panel generator for tblinc ORM Models and built-in AI Models."""

from __future__ import annotations

import json
import math
import time
from typing import Any

from ...ai_models import (
    AudioSpectrumModel,
    FormantTTSSynthesizer,
    MiniDiffusionModel,
    MiniTransformerLM,
    MusicComposerModel,
    NaiveBayesTextClassifier,
    RAGEngine,
    VideoMotionModel,
    detect_hardware,
    list_models as list_ai_models,
    run_demo as run_ai_demo,
    system_report,
)
from ..auth import LoginForm, User, authenticate, login, logout, staff_required
from ..forms import ModelForm
from ..http import Http400, Http403, Http404, Http429, JsonResponse, RedirectResponse, Request, Response
from ..orm import DoesNotExist, Model, PasswordField, ValidationError
from .quota import (
    AIKey,
    BillingTransaction,
    ModelQuota,
    TokenUsageLog,
    authenticate_api_key,
    check_quota,
    ensure_default_quotas,
    estimate_tokens,
    get_quota_overview,
    mask_api_key,
    record_token_usage,
)
from .settings_store import AppSetting, get_app_settings, update_app_settings
from .trainer import (
    TrainingRun,
    get_training_presets,
    load_or_fit_live_model,
    predict_from_training_run,
    train_and_persist_model,
)

_SIDEBAR_MODEL_META: dict[str, tuple[str, str]] = {
    "user": ("Users", "users"),
    "trainingrun": ("Jobs", "cpu"),
    "aikey": ("Keys", "key"),
    "modelquota": ("Quotas", "gauge"),
    "tokenusagelog": ("Usage", "bar-chart-3"),
    "billingtransaction": ("Transactions", "receipt"),
    "aiexperiment": ("Experiments", "flask-conical"),
    "inferencelog": ("Logs", "scroll-text"),
    "datasetrecord": ("Datasets", "database"),
}


class ModelAdmin:
    """Optional customization class for how an ORM Model appears in the Admin Panel."""

    list_display: tuple[str, ...] = ()
    search_fields: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()
    ordering: tuple[str, ...] = ("-id",)
    per_page: int = 20

    def __init__(self, model: type[Model]) -> None:
        self.model = model

    def get_list_display(self) -> list[str]:
        if self.list_display:
            return list(self.list_display)
        cols: list[str] = []
        for fname, field in self.model._fields.items():
            if isinstance(field, PasswordField):
                continue
            cols.append(fname)
            if len(cols) >= 6:
                break
        return cols

    def get_search_fields(self) -> list[str]:
        if self.search_fields:
            return list(self.search_fields)
        return [
            fname
            for fname, field in self.model._fields.items()
            if not isinstance(field, PasswordField) and field.sql_type == "TEXT"
        ]

    def get_form(self, data: dict[str, Any] | None = None, instance: Model | None = None) -> ModelForm:
        return ModelForm(data=data, instance=instance, model=self.model, exclude=self.exclude)


class _AIKeyAdmin(ModelAdmin):
    list_display = ("id", "name", "owner_username", "provider", "allowed_models", "tokens_used", "token_quota", "is_active")
    search_fields = ("name", "owner_username", "provider", "allowed_models")


class _ModelQuotaAdmin(ModelAdmin):
    list_display = ("id", "model_key", "tokens_used", "token_limit", "requests_used", "request_limit", "is_enabled")
    search_fields = ("model_key",)


class _TokenUsageAdmin(ModelAdmin):
    list_display = ("id", "model_key", "key_name", "prompt_tokens", "completion_tokens", "total_tokens", "status", "created_at")
    search_fields = ("model_key", "key_name", "username", "status")


class _BillingTransactionAdmin(ModelAdmin):
    list_display = ("id", "reference_id", "username", "tx_type", "amount_usd", "balance_after_usd", "tokens_added", "status", "created_at")
    search_fields = ("reference_id", "username", "tx_type", "description", "status")


class AdminSite:
    """Automatically generates a ready-to-use Tailwind/Lucide/Motion Admin Panel for all registered models."""

    def __init__(self, title: str = "tblinc AI Admin", prefix: str = "/admin") -> None:
        self.title = title
        self.prefix = prefix.rstrip("/") or "/admin"
        self._registry: dict[str, ModelAdmin] = {}

    def register(
        self,
        model: type[Model],
        admin_class: type[ModelAdmin] | None = None,
    ) -> Any:
        slug = model._meta["model_name"]
        admin_obj = (admin_class or ModelAdmin)(model)
        self._registry[slug] = admin_obj
        return model

    def get_admin(self, slug: str) -> ModelAdmin:
        if slug not in self._registry:
            raise Http404(f"Model '{slug}' is not registered in the Admin Panel.")
        return self._registry[slug]

    def _sidebar_models(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for slug, madmin in self._registry.items():
            m = madmin.model
            label, icon = _SIDEBAR_MODEL_META.get(slug, (m._meta["verbose_name_plural"], "table-2"))
            items.append(
                {
                    "slug": slug,
                    "table": m._meta["table"],
                    "label": label,
                    "icon": icon,
                    "verbose_name": m._meta["verbose_name"],
                    "verbose_plural": m._meta["verbose_name_plural"],
                    "count": m.objects.count(),
                }
            )
        return items

    def _base_ctx(self, request: Request) -> dict[str, Any]:
        import os

        ensure_default_quotas()
        sidebar = self._sidebar_models()
        db_path = str(getattr(getattr(request, "app", None), "db", None).path if getattr(request, "app", None) else ":memory:")
        db_size_kb = 0.0
        if db_path and db_path != ":memory:" and os.path.isfile(db_path):
            db_size_kb = round(os.path.getsize(db_path) / 1024.0, 1)
        db_size_display = f"{db_size_kb} KB" if db_size_kb > 0 else "In-Memory SQLite"

        users = User.objects.all()
        total_balance = round(sum(float(getattr(u, "balance_usd", 0.0) or 0.0) for u in users), 2)
        total_spent = round(sum(float(getattr(u, "total_spent_usd", 0.0) or 0.0) for u in users), 4)
        txs = BillingTransaction.objects.all()
        total_credited = round(sum(float(t.amount_usd or 0.0) for t in txs if float(t.amount_usd or 0.0) > 0), 2)
        q_summary = get_quota_overview()["summary"]

        return {
            "admin_title": self.title,
            "admin_prefix": self.prefix,
            "registered_models": sidebar,
            "total_models": len(sidebar),
            "total_records": sum(item["count"] for item in sidebar),
            "ai_model_count": len(list_ai_models()),
            "current_user": request.user,
            "db_stats": {
                "db_path": db_path,
                "db_size_display": db_size_display,
                "user_count": len(users),
                "total_balance_usd": f"{total_balance:.2f}",
                "total_spent_usd": f"{total_spent:.4f}",
                "total_credited_usd": f"{total_credited:.2f}",
                "transaction_count": len(txs),
                "active_keys": q_summary["active_keys"],
                "total_keys": q_summary["total_keys"],
                "total_tokens": q_summary["total_tokens_used"],
                "total_requests": q_summary["total_requests"],
                "training_count": TrainingRun.objects.count(),
            },
        }

    def mount(self, app: Any) -> None:
        """Register all Admin Panel routes + AI Studio endpoints onto a TblincApp."""
        prefix = self.prefix
        # Always include User, TrainingRun, AIKey, ModelQuota, and TokenUsageLog automatically
        if User._meta["model_name"] not in self._registry:
            self.register(User)
        if TrainingRun._meta["model_name"] not in self._registry:
            self.register(TrainingRun)
        if AIKey._meta["model_name"] not in self._registry:
            self.register(AIKey, _AIKeyAdmin)
        if ModelQuota._meta["model_name"] not in self._registry:
            self.register(ModelQuota, _ModelQuotaAdmin)
        if TokenUsageLog._meta["model_name"] not in self._registry:
            self.register(TokenUsageLog, _TokenUsageAdmin)
        if BillingTransaction._meta["model_name"] not in self._registry:
            self.register(BillingTransaction, _BillingTransactionAdmin)

        @app.route(f"{prefix}/login/", methods=("GET", "POST"), name="admin:login")
        def admin_login(request: Request) -> Response:
            from ..auth.service import purge_default_fake_admin

            purge_default_fake_admin()
            next_url = request.GET.get("next") or request.POST.get("next") or f"{prefix}/"
            form = LoginForm(request.POST if request.method == "POST" else None)
            if request.method == "POST" and form.is_valid():
                user = authenticate(form.cleaned_data["username"], form.cleaned_data["password"])
                if user is not None and (user.is_staff or user.is_superuser):
                    login(request, user)
                    return RedirectResponse(next_url)
                form.errors["__all__"] = "Valid staff or superuser credentials required."
            return app.render(
                request,
                "tblinc_auth.html",
                {
                    "title": f"{self.title} Login",
                    "subtitle": "Sign in with a staff or superuser account to manage application data.",
                    "button_label": "Enter Admin Panel",
                    "form_html": form.as_html(),
                    "next_url": next_url,
                },
            )

        @app.route(f"{prefix}/logout/", methods=("GET", "POST"), name="admin:logout")
        def admin_logout(request: Request) -> Response:
            logout(request)
            return RedirectResponse(f"{prefix}/login/")

        @app.route(f"{prefix}/", methods=("GET",), name="admin:dashboard")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_dashboard(request: Request) -> Response:
            recent_users = [u.to_dict() for u in User.objects.order_by("-id").limit(8).all()]
            recent_txs = [t.to_dict() for t in BillingTransaction.objects.order_by("-id").limit(8).all()]
            ctx = {
                **self._base_ctx(request),
                "recent_users": recent_users,
                "recent_transactions": recent_txs,
            }
            return app.render(request, "tblinc_admin_dashboard.html", ctx)

        @app.route(f"{prefix}/ai/", methods=("GET",), name="admin:ai_studio")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_ai_studio(request: Request) -> Response:
            models = []
            for meta in list_ai_models():
                entry = dict(meta)
                entry["input_json"] = json.dumps(meta.get("input_example") or {})
                models.append(entry)
            ctx = {**self._base_ctx(request), "ai_models": models}
            return app.render(request, "tblinc_admin_ai.html", ctx)

        @app.route(f"{prefix}/models/", methods=("GET",), name="admin:models")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_model_hub(request: Request) -> Response:
            all_meta = list_ai_models()
            selected_cat = request.GET.get("category", "").strip()
            categories = sorted({m["category"] for m in all_meta})
            models = []
            for meta in all_meta:
                if selected_cat and meta["category"] != selected_cat:
                    continue
                entry = dict(meta)
                entry["input_json"] = json.dumps(meta.get("input_example") or {})
                models.append(entry)
            ctx = {
                **self._base_ctx(request),
                "ai_models": models,
                "categories": categories,
                "selected_category": selected_cat,
            }
            return app.render(request, "tblinc_admin_models.html", ctx)

        @app.route(f"{prefix}/catalog/", methods=("GET",), name="admin:catalog")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_catalog_redirect(request: Request) -> Response:
            cat = request.GET.get("category", "").strip()
            target = f"{prefix}/models/?category={cat}" if cat else f"{prefix}/models/"
            return RedirectResponse(target)

        @app.route(f"{prefix}/train/", methods=("GET",), name="admin:train")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_train_page(request: Request) -> Response:
            runs = TrainingRun.objects.order_by("-id").limit(25).all()
            ctx = {
                **self._base_ctx(request),
                "ai_models": list_ai_models(),
                "training_runs": runs,
                "presets_json": json.dumps(get_training_presets()),
                "hardware": detect_hardware(),
            }
            return app.render(request, "tblinc_admin_train.html", ctx)

        @app.route(f"{prefix}/keys/", methods=("GET",), name="admin:keys")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_keys_page(request: Request) -> Response:
            overview = get_quota_overview()
            ctx = {
                **self._base_ctx(request),
                "ai_models": list_ai_models(),
                "summary": overview["summary"],
                "api_keys": overview["keys"],
                "model_quotas": overview["quotas"],
                "usage_logs": overview["recent_usage"],
            }
            return app.render(request, "tblinc_admin_keys.html", ctx)

        @app.route(f"{prefix}/settings/", methods=("GET",), name="admin:settings")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_settings_page(request: Request) -> Response:
            cfg = get_app_settings(app=app)
            hw = detect_hardware()
            ctx = {
                **self._base_ctx(request),
                "ai_models": list_ai_models(),
                "cfg": cfg,
                "hardware": hw,
                "db_path": str(app.db.path),
            }
            return app.render(request, "tblinc_admin_settings.html", ctx)

        @app.route("/api/admin/settings", methods=("GET", "POST"), name="api:admin_settings")
        def api_admin_settings(request: Request) -> Response:
            if request.user is None or not (request.user.is_staff or request.user.is_superuser):
                raise Http403("Admin/staff login required to manage settings.")
            if request.method == "GET":
                return JsonResponse({"ok": True, "settings": get_app_settings(app=app)})
            payload = request.json() if request.body else {}
            updated = update_app_settings(payload if isinstance(payload, dict) else {}, app=app)
            return JsonResponse({"ok": True, "settings": updated})

        def _require_staff_api(request: Request, msg: str = "Admin/staff login required.") -> None:
            if request.user is None or not (request.user.is_staff or request.user.is_superuser):
                raise Http403(msg)

        @app.route("/api/ai/keys", methods=("GET", "POST"), name="api:ai_keys")
        def api_ai_keys(request: Request) -> Response:
            _require_staff_api(request, "Admin/staff login required to manage AI keys.")
            if request.method == "GET":
                overview = get_quota_overview()
                return JsonResponse({"count": len(overview["keys"]), "keys": overview["keys"]})

            payload = request.json() if request.body else {}
            name = str(payload.get("name", "")).strip() or "New AI Key"
            provider = str(payload.get("provider", "tblinc")).strip().lower()
            raw_key = str(payload.get("api_key", "")).strip()
            base_url = str(payload.get("base_url", "")).strip()
            allowed = str(payload.get("allowed_models", "*")).strip() or "*"
            try:
                token_quota = max(0, int(payload.get("token_quota", 100_000)))
                request_quota = max(0, int(payload.get("request_quota", 1_000)))
            except (TypeError, ValueError) as exc:
                raise Http400("token_quota and request_quota must be non-negative integers.") from exc

            owner_username = str(
                payload.get("owner_username") or (request.user.username if request.user else "admin")
            ).strip()
            key_obj = AIKey(
                name=name,
                owner_username=owner_username,
                provider=provider,
                api_key=raw_key,
                base_url=base_url,
                allowed_models=allowed,
                token_quota=token_quota,
                request_quota=request_quota,
                is_active=True,
            )
            key_obj.save()
            data = key_obj.masked_dict()
            data["api_key"] = key_obj.api_key  # Returned once upon creation so admin can copy it
            return JsonResponse({"ok": True, "key": data}, status=201)

        @app.route("/api/ai/keys/<int:key_id>/toggle", methods=("POST",), name="api:ai_key_toggle")
        def api_ai_key_toggle(request: Request, key_id: int) -> Response:
            _require_staff_api(request, "Admin/staff login required to toggle AI keys.")
            try:
                key_obj = AIKey.objects.get(id=key_id)
            except DoesNotExist as exc:
                raise Http404(f"AIKey #{key_id} not found.") from exc
            key_obj.is_active = not bool(key_obj.is_active)
            key_obj.save()
            return JsonResponse({"ok": True, "key": key_obj.masked_dict()})

        @app.route("/api/ai/keys/<int:key_id>/reset", methods=("POST",), name="api:ai_key_reset")
        def api_ai_key_reset(request: Request, key_id: int) -> Response:
            _require_staff_api(request, "Admin/staff login required to reset AI key usage.")
            try:
                key_obj = AIKey.objects.get(id=key_id)
            except DoesNotExist as exc:
                raise Http404(f"AIKey #{key_id} not found.") from exc
            key_obj.tokens_used = 0
            key_obj.requests_used = 0
            key_obj.save()
            return JsonResponse({"ok": True, "key": key_obj.masked_dict()})

        @app.route("/api/ai/keys/<int:key_id>", methods=("DELETE",), name="api:ai_key_delete")
        def api_ai_key_delete(request: Request, key_id: int) -> Response:
            _require_staff_api(request, "Admin/staff login required to delete AI keys.")
            try:
                key_obj = AIKey.objects.get(id=key_id)
            except DoesNotExist as exc:
                raise Http404(f"AIKey #{key_id} not found.") from exc
            key_obj.delete()
            return JsonResponse({"ok": True, "deleted": key_id})

        @app.route("/api/ai/quotas", methods=("GET", "POST"), name="api:ai_quotas")
        def api_ai_quotas(request: Request) -> Response:
            _require_staff_api(request, "Admin/staff login required to manage AI token quotas.")
            if request.method == "GET":
                return JsonResponse(get_quota_overview())

            payload = request.json() if request.body else {}
            model_key = str(payload.get("model_key", "*")).strip() or "*"
            try:
                token_limit = max(0, int(payload.get("token_limit", 250_000)))
                request_limit = max(0, int(payload.get("request_limit", 2_000)))
                cost_per_1k = max(0.0, float(payload.get("cost_per_1k_tokens", 0.002)))
            except (TypeError, ValueError) as exc:
                raise Http400("Invalid numeric quota values.") from exc
            is_enabled = bool(payload.get("is_enabled", True))

            try:
                q_obj = ModelQuota.objects.get(model_key=model_key)
                q_obj.token_limit = token_limit
                q_obj.request_limit = request_limit
                q_obj.cost_per_1k_tokens = cost_per_1k
                q_obj.is_enabled = is_enabled
                q_obj.save()
            except DoesNotExist:
                q_obj = ModelQuota.objects.create(
                    model_key=model_key,
                    token_limit=token_limit,
                    request_limit=request_limit,
                    cost_per_1k_tokens=cost_per_1k,
                    is_enabled=is_enabled,
                )
            return JsonResponse({"ok": True, "quota": q_obj.to_dict()})

        @app.route("/api/ai/quotas/reset", methods=("POST",), name="api:ai_quotas_reset")
        def api_ai_quotas_reset(request: Request) -> Response:
            _require_staff_api(request, "Admin/staff login required to reset AI quotas.")
            payload = request.json() if request.body else {}
            target_key = str(payload.get("model_key", "")).strip()
            rows = (
                ModelQuota.objects.filter(model_key=target_key).all()
                if target_key
                else ModelQuota.objects.all()
            )
            for row in rows:
                row.tokens_used = 0
                row.requests_used = 0
                row.save()
            return JsonResponse({"ok": True, "reset_count": len(rows)})

        @app.route("/api/ai/usage", methods=("GET",), name="api:ai_usage")
        def api_ai_usage(request: Request) -> Response:
            _require_staff_api(request, "Admin/staff login required to view AI token usage.")
            overview = get_quota_overview()
            return JsonResponse({"summary": overview["summary"], "recent_usage": overview["recent_usage"]})

        @app.route("/api/ai/train", methods=("POST",), name="api:ai_train")
        def api_ai_train(request: Request) -> Response:
            if request.user is None or not (request.user.is_staff or request.user.is_superuser):
                raise Http403("Admin/staff login required to train models.")
            payload = request.json() if request.body else {}
            model_key = str(payload.get("model_key", "")).strip()
            if not model_key:
                raise Http400("model_key is required.")
            username = request.user.username
            p_tokens = estimate_tokens(payload.get("dataset") or payload, modality=model_key)
            check_quota(model_key, prompt_tokens=p_tokens, username=username)
            try:
                run = train_and_persist_model(
                    model_key=model_key,
                    run_name=str(payload.get("run_name", "")),
                    hyperparams=payload.get("hyperparams") or {},
                    dataset=payload.get("dataset") or {},
                    device_pref=str(payload.get("device", "auto")),
                )
            except KeyError as exc:
                raise Http404(str(exc)) from exc
            except (ValueError, TypeError) as exc:
                raise Http400(str(exc)) from exc
            c_tokens = estimate_tokens(run.metrics, modality=model_key)
            usage = record_token_usage(
                model_key,
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                latency_ms=float(run.duration_ms or 0.0),
                username=username,
            )
            exp_admin = self._registry.get("aiexperiment")
            if exp_admin is not None:
                try:
                    metrics_d = run.metrics if isinstance(run.metrics, dict) else {}
                    score = float(
                        metrics_d.get("accuracy")
                        or metrics_d.get("r2_score")
                        or metrics_d.get("top1_retrieval_accuracy")
                        or metrics_d.get("confidence")
                        or 0.95
                    )
                    exp_admin.model.objects.create(
                        name=run.run_name,
                        model_key=run.model_key,
                        description=f"Trained on {run.device} ({run.duration_ms}ms) · Artifact #{run.pk}",
                        accuracy_score=round(score, 4),
                        is_active=True,
                    )
                except Exception:
                    pass
            return JsonResponse({"ok": True, "run": run.to_dict(), "usage": usage}, status=201)

        @app.route("/api/ai/train/runs", methods=("GET",), name="api:ai_train_runs")
        def api_ai_train_runs(request: Request) -> Response:
            if request.user is None or not (request.user.is_staff or request.user.is_superuser):
                raise Http403("Admin/staff login required to inspect training runs.")
            runs = [r.to_dict() for r in TrainingRun.objects.order_by("-id").limit(50).all()]
            return JsonResponse({"count": len(runs), "runs": runs})

        @app.route("/api/ai/train/<int:run_id>/predict", methods=("POST",), name="api:ai_train_predict")
        def api_ai_train_predict(request: Request, run_id: int) -> Response:
            if request.user is None or not (request.user.is_staff or request.user.is_superuser):
                raise Http403("Admin/staff login required to run saved training artifacts.")
            try:
                run = TrainingRun.objects.get(id=run_id)
            except DoesNotExist as exc:
                raise Http404(f"TrainingRun #{run_id} not found.") from exc
            payload = request.json() if request.body else {}
            custom_input = payload.get("input") if isinstance(payload, dict) else None
            try:
                output = predict_from_training_run(run, custom_input=custom_input)
            except (FileNotFoundError, ValueError, KeyError) as exc:
                raise Http400(str(exc)) from exc
            return JsonResponse(output)

        @app.route(f"{prefix}/<str:model_slug>/", methods=("GET",), name="admin:list")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_list(request: Request, model_slug: str) -> Response:
            madmin = self.get_admin(model_slug)
            model_cls = madmin.model
            q = request.GET.get("q", "").strip()
            try:
                page = max(1, int(request.GET.get("page", "1")))
            except ValueError:
                page = 1

            qs = model_cls.objects.get_queryset()
            if q:
                qs = qs.search(q, madmin.get_search_fields())
            if madmin.ordering:
                qs = qs.order_by(*madmin.ordering)

            total_count = qs.count()
            total_pages = max(1, math.ceil(total_count / madmin.per_page))
            page = min(page, total_pages)
            objects = qs.limit(madmin.per_page).offset((page - 1) * madmin.per_page).all()

            cols = madmin.get_list_display()
            rows = []
            for obj in objects:
                cells = []
                for col in cols:
                    val = getattr(obj, col, "")
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val)
                    cells.append("" if val is None else str(val))
                rows.append({"pk": obj.pk, "cells": cells})

            ctx = {
                **self._base_ctx(request),
                "model_slug": model_slug,
                "model_name": model_cls._meta["verbose_name"],
                "model_plural": model_cls._meta["verbose_name_plural"],
                "columns": [
                    model_cls._fields[c].label if c in model_cls._fields else c.replace("_", " ").title()
                    for c in cols
                ],
                "rows": rows,
                "search_query": q,
                "total_count": total_count,
                "page": page,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
                "prev_page": page - 1,
                "next_page": page + 1,
            }
            return app.render(request, "tblinc_admin_list.html", ctx)

        @app.route(f"{prefix}/<str:model_slug>/create/", methods=("GET", "POST"), name="admin:create")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_create(request: Request, model_slug: str) -> Response:
            madmin = self.get_admin(model_slug)
            form = madmin.get_form(data=request.POST if request.method == "POST" else None)
            if request.method == "POST" and form.is_valid():
                try:
                    form.save()
                    return RedirectResponse(f"{prefix}/{model_slug}/")
                except ValidationError as exc:
                    form.errors.update(exc.errors)
            ctx = {
                **self._base_ctx(request),
                "action": "Create",
                "model_slug": model_slug,
                "model_name": madmin.model._meta["verbose_name"],
                "form_html": form.as_html(),
            }
            return app.render(request, "tblinc_admin_form.html", ctx)

        @app.route(f"{prefix}/<str:model_slug>/<int:pk>/edit/", methods=("GET", "POST"), name="admin:edit")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_edit(request: Request, model_slug: str, pk: int) -> Response:
            madmin = self.get_admin(model_slug)
            try:
                obj = madmin.model.objects.get(id=pk)
            except DoesNotExist as exc:
                raise Http404(f"{madmin.model.__name__} #{pk} not found.") from exc
            form = madmin.get_form(data=request.POST if request.method == "POST" else None, instance=obj)
            if request.method == "POST" and form.is_valid():
                try:
                    form.save()
                    return RedirectResponse(f"{prefix}/{model_slug}/")
                except ValidationError as exc:
                    form.errors.update(exc.errors)
            ctx = {
                **self._base_ctx(request),
                "action": f"Edit #{pk}",
                "model_slug": model_slug,
                "model_name": madmin.model._meta["verbose_name"],
                "form_html": form.as_html(),
            }
            return app.render(request, "tblinc_admin_form.html", ctx)

        @app.route(f"{prefix}/<str:model_slug>/<int:pk>/delete/", methods=("GET", "POST"), name="admin:delete")
        @staff_required(login_url=f"{prefix}/login/")
        def admin_delete(request: Request, model_slug: str, pk: int) -> Response:
            madmin = self.get_admin(model_slug)
            try:
                obj = madmin.model.objects.get(id=pk)
            except DoesNotExist as exc:
                raise Http404(f"{madmin.model.__name__} #{pk} not found.") from exc
            if request.method == "POST":
                obj.delete()
                return RedirectResponse(f"{prefix}/{model_slug}/")
            ctx = {
                **self._base_ctx(request),
                "model_slug": model_slug,
                "model_name": madmin.model._meta["verbose_name"],
                "object_pk": pk,
                "object_str": str(obj),
            }
            return app.render(request, "tblinc_admin_delete.html", ctx)

        # Built-in JSON AI API endpoints powering both Main Site (/) and Admin AI Studio (/admin/ai/)
        @app.route("/api/ai/", methods=("GET",), name="api:ai_list")
        def api_ai_list(request: Request) -> Response:
            models = list_ai_models()
            return JsonResponse({"count": len(models), "models": models})

        def _check_studio_key(request: Request, model_key: str) -> AIKey | None:
            api_key_obj = authenticate_api_key(request, model_key=model_key)
            cfg = get_app_settings(app=app)
            if cfg.get("require_studio_api_key_bool"):
                is_staff = request.user is not None and (request.user.is_staff or request.user.is_superuser)
                if api_key_obj is None and not is_staff:
                    raise Http403("tblinc AI requires a valid X-API-Key / Bearer token (enabled in Admin Settings).")
            return api_key_obj

        def _record_inference_log(
            model_key: str,
            input_payload: Any,
            output_prediction: Any,
            confidence: float = 1.0,
            latency_ms: float = 0.0,
        ) -> None:
            madmin = self._registry.get("inferencelog")
            if madmin is None:
                return
            try:
                madmin.model.objects.create(
                    model_key=model_key,
                    input_payload=input_payload if isinstance(input_payload, dict) else {"value": input_payload},
                    output_prediction=str(output_prediction or "")[:500],
                    confidence=round(float(confidence or 0.0), 4),
                    latency_ms=round(float(latency_ms or 0.0), 2),
                )
            except Exception:
                pass

        def _resolve_caller_username(request: Request, api_key_obj: AIKey | None, fallback: str = "anonymous") -> str:
            if request.user is not None:
                return request.user.username
            if api_key_obj is not None:
                return (api_key_obj.owner_username or api_key_obj.name or fallback).strip() or fallback
            return fallback

        @app.route("/api/ai/chat", methods=("POST",), name="api:ai_chat")
        def api_ai_chat(request: Request) -> Response:
            t0 = time.perf_counter()
            payload = request.json() if request.body else {}
            message = str(payload.get("message", "")).strip() or "Tell me about tblinc AI."
            mode = str(payload.get("mode", "assistant")).lower()

            api_key_obj = _check_studio_key(request, "chat")
            username = _resolve_caller_username(request, api_key_obj)
            p_tokens = estimate_tokens(message, modality="text")
            check_quota("chat", prompt_tokens=p_tokens, api_key_obj=api_key_obj, username=username)

            rag, rag_source = load_or_fit_live_model("search")
            rag_res = rag.predict({"query": message, "top_k": 2}).to_dict()
            hits = rag_res.get("details", {}).get("hits", [])

            sent, _ = load_or_fit_live_model("sentiment")
            sentiment = sent.predict({"text": message}).prediction

            lm, lm_source = load_or_fit_live_model("chat")
            lm_res = lm.predict(
                {
                    "prompt": message,
                    "max_tokens": 24,
                    "temperature": 0.7,
                    "conversational": (mode != "creative"),
                }
            ).to_dict()

            if mode == "creative":
                reply = lm_res["prediction"]
                source = f"chat ({lm_source})"
            elif mode == "rag":
                best = hits[0]["text"] if hits else lm_res["prediction"]
                reply = f"{best}"
                source = f"search ({rag_source})" if hits else f"chat ({lm_source})"
            elif lm_res.get("details", {}).get("mode") == "instruction_transformer":
                reply = lm_res["prediction"]
                source = f"chat ({lm_source})"
            elif hits and hits[0].get("score", 0.0) >= 1.2:
                reply = f"{hits[0]['text']}"
                source = f"search ({rag_source})"
            else:
                reply = lm_res["prediction"]
                source = f"chat ({lm_source})"

            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            c_tokens = estimate_tokens(reply, modality="text")
            usage = record_token_usage(
                "chat",
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                latency_ms=elapsed_ms,
                api_key_obj=api_key_obj,
                username=username,
            )
            _record_inference_log("chat", {"message": message, "mode": mode}, reply, 0.96, elapsed_ms)
            return JsonResponse(
                {
                    "reply": reply,
                    "mode": mode,
                    "source": source,
                    "sentiment": sentiment,
                    "hits": hits,
                    "latency_ms": elapsed_ms,
                    "usage": usage,
                }
            )

        @app.route("/api/ai/image", methods=("POST",), name="api:ai_image")
        def api_ai_image(request: Request) -> Response:
            t0 = time.perf_counter()
            payload = request.json() if request.body else {}
            inp = {
                "prompt": str(payload.get("prompt", "neon star")),
                "style": str(payload.get("style", "neon")),
                "steps": int(payload.get("steps", 12)),
                "guidance": float(payload.get("guidance", 1.5)),
                "seed": int(payload.get("seed", 42)),
            }
            api_key_obj = _check_studio_key(request, "image")
            username = _resolve_caller_username(request, api_key_obj)
            p_tokens = estimate_tokens(inp, modality="image")
            check_quota("image", prompt_tokens=p_tokens, api_key_obj=api_key_obj, username=username)

            model, ckpt_source = load_or_fit_live_model("image")
            pred = model.predict(inp)
            out = {"training": model.training_metrics, "checkpoint": ckpt_source, "result": pred.to_dict()}
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            out["usage"] = record_token_usage(
                "image",
                prompt_tokens=p_tokens,
                completion_tokens=estimate_tokens(out.get("result"), modality="image"),
                latency_ms=elapsed_ms,
                api_key_obj=api_key_obj,
                username=username,
            )
            res = out.get("result") or {}
            _record_inference_log("image", inp, res.get("prediction", inp["prompt"]), float(res.get("confidence") or 0.95), elapsed_ms)
            return JsonResponse(out)

        @app.route("/api/ai/video", methods=("POST",), name="api:ai_video")
        def api_ai_video(request: Request) -> Response:
            t0 = time.perf_counter()
            payload = request.json() if request.body else {}
            api_key_obj = _check_studio_key(request, "video")
            username = _resolve_caller_username(request, api_key_obj)
            p_tokens = estimate_tokens(payload, modality="video")
            check_quota("video", prompt_tokens=p_tokens, api_key_obj=api_key_obj, username=username)

            model, ckpt_source = load_or_fit_live_model("video")
            seq = model.synthesize_sequence(
                prompt=str(payload.get("prompt", "neon wave")),
                motion=str(payload.get("motion", "pan_right")),
                num_frames=int(payload.get("frames", 24)),
                fps=int(payload.get("fps", 12)),
            )
            seq["checkpoint"] = ckpt_source
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            seq["latency_ms"] = elapsed_ms
            seq["usage"] = record_token_usage(
                "video",
                prompt_tokens=p_tokens,
                completion_tokens=estimate_tokens({"frames": seq.get("num_frames")}, modality="video"),
                latency_ms=elapsed_ms,
                api_key_obj=api_key_obj,
                username=username,
            )
            _record_inference_log("video", payload, f"{seq.get('prompt')} ({seq.get('num_frames')} frames)", 0.94, elapsed_ms)
            return JsonResponse(seq)

        @app.route("/api/ai/audio", methods=("POST",), name="api:ai_audio")
        def api_ai_audio(request: Request) -> Response:
            t0 = time.perf_counter()
            payload = request.json() if request.body else {}
            tts_inp = {
                "text": str(payload.get("text", "Welcome to tblinc AI.")),
                "voice": str(payload.get("voice", "neutral")),
                "pitch_hz": float(payload.get("pitch_hz", 165.0)),
                "speed": float(payload.get("speed", 1.0)),
            }
            api_key_obj = _check_studio_key(request, "voice")
            username = _resolve_caller_username(request, api_key_obj)
            p_tokens = estimate_tokens(tts_inp, modality="voice")
            check_quota("voice", prompt_tokens=p_tokens, api_key_obj=api_key_obj, username=username)

            tts, ckpt_source = load_or_fit_live_model("voice")
            tts_pred = tts.predict(tts_inp)
            tts_out: dict[str, Any] = {
                "training": tts.training_metrics,
                "checkpoint": ckpt_source,
                "result": tts_pred.to_dict(),
            }

            aud, _ = load_or_fit_live_model("audio")
            aud_pred = aud.predict({"freq_hz": tts_inp["pitch_hz"], "sample_rate": 1000})
            tts_out["spectrum_analysis"] = aud_pred.to_dict()
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            tts_out["usage"] = record_token_usage(
                "voice",
                prompt_tokens=p_tokens,
                completion_tokens=estimate_tokens(tts_out.get("result"), modality="voice"),
                latency_ms=elapsed_ms,
                api_key_obj=api_key_obj,
                username=username,
            )
            _record_inference_log("voice", tts_inp, tts_inp["text"], 0.97, elapsed_ms)
            return JsonResponse(tts_out)

        @app.route("/api/ai/music", methods=("POST",), name="api:ai_music")
        def api_ai_music(request: Request) -> Response:
            t0 = time.perf_counter()
            payload = request.json() if request.body else {}
            inp = {
                "mood": str(payload.get("mood", "synthwave")),
                "bpm": int(payload.get("bpm", 112)),
                "duration_sec": float(payload.get("duration_sec", 4.0)),
                "seed": int(payload.get("seed", 42)),
            }
            api_key_obj = _check_studio_key(request, "music")
            username = _resolve_caller_username(request, api_key_obj)
            p_tokens = estimate_tokens(inp, modality="music")
            check_quota("music", prompt_tokens=p_tokens, api_key_obj=api_key_obj, username=username)

            composer, ckpt_source = load_or_fit_live_model("music")
            mus_pred = composer.predict(inp)
            out = {"training": composer.training_metrics, "checkpoint": ckpt_source, "result": mus_pred.to_dict()}
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            out["usage"] = record_token_usage(
                "music",
                prompt_tokens=p_tokens,
                completion_tokens=estimate_tokens(out.get("result"), modality="music"),
                latency_ms=elapsed_ms,
                api_key_obj=api_key_obj,
                username=username,
            )
            _record_inference_log("music", inp, f"{inp['mood']} ({inp['bpm']} BPM)", 0.95, elapsed_ms)
            return JsonResponse(out)

        @app.route("/api/ai/<str:model_key>/run", methods=("POST",), name="api:ai_run")
        def api_ai_run(request: Request, model_key: str) -> Response:
            api_key_obj = authenticate_api_key(request, model_key=model_key)
            is_staff = request.user is not None and (request.user.is_staff or request.user.is_superuser)
            if api_key_obj is None and not is_staff:
                raise Http403("Admin/staff login or valid X-API-Key / Bearer token required to run AI Model Hub.")

            t0 = time.perf_counter()
            payload = request.json() if request.body else {}
            custom_input = payload.get("input") if isinstance(payload, dict) else None
            username = _resolve_caller_username(request, api_key_obj, fallback="api")
            p_tokens = estimate_tokens(custom_input, modality=model_key)
            check_quota(model_key, prompt_tokens=p_tokens, api_key_obj=api_key_obj, username=username)

            try:
                live_model, ckpt_source = load_or_fit_live_model(model_key)
                inp = custom_input if custom_input is not None else live_model.metadata.input_example
                pred = live_model.predict(inp)
                output = {
                    "training": live_model.training_metrics,
                    "checkpoint": ckpt_source,
                    "model": live_model.metadata.to_dict(),
                    "result": pred.to_dict(),
                }
            except KeyError as exc:
                raise Http404(str(exc)) from exc

            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            output["usage"] = record_token_usage(
                model_key,
                prompt_tokens=p_tokens,
                completion_tokens=estimate_tokens(output.get("result"), modality=model_key),
                latency_ms=elapsed_ms,
                api_key_obj=api_key_obj,
                username=username,
            )
            res = output.get("result") or {}
            _record_inference_log(model_key, custom_input, res.get("prediction", ""), float(res.get("confidence") or 0.9), elapsed_ms)
            return JsonResponse(output)

        @app.route("/api/system/", methods=("GET",), name="api:system")
        def api_system(request: Request) -> Response:
            report = system_report()
            report["ai_model_count"] = len(list_ai_models())
            report["quota_summary"] = get_quota_overview()["summary"]
            return JsonResponse(report)
