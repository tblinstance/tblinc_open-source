"""Admin AI API Keys, Per-Model Token Quotas, and Live Token Usage Metering across all AI models."""

from __future__ import annotations

import json
import math
import secrets
from typing import Any

from ...ai_models import list_models, registry
from ..http import Http403, Http429, Request
from ..orm import BooleanField, CharField, DateTimeField, DoesNotExist, FloatField, IntegerField, Model

_PROVIDER_CHOICES: list[tuple[str, str]] = [
    ("tblinc", "tblinc API Key (Gateway)"),
    ("openai", "OpenAI"),
    ("anthropic", "Anthropic Claude"),
    ("gemini", "Google Gemini"),
    ("huggingface", "Hugging Face"),
    ("custom", "Custom / Local Ollama"),
]

_QUOTA_MODEL_CHOICES: list[tuple[str, str]] = [("*", "* — Global Default (All AI Models)")] + [
    (m["key"], f"{m['name']} ({m['key']})") for m in list_models()
]


def generate_tblinc_key() -> str:
    """Generate a high-entropy tblinc gateway API key."""
    return f"tbl_sk_{secrets.token_hex(18)}"


def mask_api_key(raw: str) -> str:
    """Safely mask secret API keys for display in Admin tables and JSON responses."""
    text = str(raw or "").strip()
    if len(text) <= 10:
        return "••••" if text else ""
    return f"{text[:10]}••••{text[-4:]}"


class AIKey(Model):
    """Admin or user-managed AI API key (tblinc gateway key or external provider key) with token & request quotas."""

    name = CharField(max_length=120, placeholder="Production AI Key")
    owner_username = CharField(
        max_length=120,
        blank=True,
        default="",
        verbose_name="Owner",
        placeholder="username (blank = admin/system)",
    )
    provider = CharField(max_length=32, choices=_PROVIDER_CHOICES, default="tblinc")
    api_key = CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="API Key",
        placeholder="Leave blank to auto-generate tbl_sk_...",
        help_text="Auto-generates a secure tbl_sk_... key when left blank for tblinc keys.",
    )
    base_url = CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Base URL",
        placeholder="Optional: https://api.openai.com/v1 or http://localhost:11434/v1",
    )
    allowed_models = CharField(
        max_length=255,
        blank=True,
        default="*",
        help_text="'*' for all AI models, or comma-separated keys (e.g. chat,image,voice,music).",
    )
    token_quota = IntegerField(default=100_000, help_text="Maximum total tokens allowed (0 = unlimited).")
    tokens_used = IntegerField(default=0)
    request_quota = IntegerField(default=1_000, help_text="Maximum requests allowed (0 = unlimited).")
    requests_used = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        table_name = "tblinc_ai_keys"
        verbose_name = "Key"
        verbose_name_plural = "Keys"

    def save(self, db: Any = None) -> AIKey:
        if not str(self.api_key or "").strip() and self.provider == "tblinc":
            self.api_key = generate_tblinc_key()
        if not str(self.allowed_models or "").strip():
            self.allowed_models = "*"
        return super().save(db=db)

    def allows_model(self, model_key: str) -> bool:
        raw = str(self.allowed_models or "*").strip()
        if not raw or raw == "*":
            return True
        canonical = registry.resolve_key(model_key)
        allowed = {registry.resolve_key(tok.strip()) for tok in raw.split(",") if tok.strip()}
        return "*" in allowed or canonical in allowed or model_key in allowed

    def masked_dict(self) -> dict[str, Any]:
        t_limit = int(self.token_quota or 0)
        t_used = int(self.tokens_used or 0)
        r_limit = int(self.request_quota or 0)
        r_used = int(self.requests_used or 0)
        return {
            "id": self.pk,
            "name": self.name,
            "owner_username": self.owner_username or "admin",
            "provider": self.provider,
            "masked_key": mask_api_key(self.api_key),
            "base_url": self.base_url,
            "allowed_models": self.allowed_models,
            "token_quota": t_limit,
            "tokens_used": t_used,
            "tokens_remaining": max(0, t_limit - t_used) if t_limit > 0 else None,
            "token_pct": min(100, round((t_used / t_limit) * 100)) if t_limit > 0 else 0,
            "request_quota": r_limit,
            "requests_used": r_used,
            "is_active": bool(self.is_active),
            "created_at": str(self.created_at or ""),
        }


class ModelQuota(Model):
    """Per-model (or global '*') token & request quota policy managed from the Admin Panel."""

    model_key = CharField(
        max_length=64,
        unique=True,
        choices=_QUOTA_MODEL_CHOICES,
        default="*",
        verbose_name="AI Model",
        help_text="Choose '*' for global quota across all models or a specific AI model.",
    )
    token_limit = IntegerField(default=500_000, help_text="Max total tokens (0 = unlimited).")
    request_limit = IntegerField(default=5_000, help_text="Max total requests (0 = unlimited).")
    tokens_used = IntegerField(default=0)
    requests_used = IntegerField(default=0)
    cost_per_1k_tokens = FloatField(default=0.002, help_text="Estimated USD cost per 1,000 tokens.")
    is_enabled = BooleanField(default=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        table_name = "tblinc_model_quotas"
        verbose_name = "Quota"
        verbose_name_plural = "Quotas"


class TokenUsageLog(Model):
    """Audit ledger recording prompt, completion & total token usage for every AI model execution."""

    model_key = CharField(max_length=64, verbose_name="AI Model")
    key_name = CharField(max_length=120, blank=True, default="session")
    username = CharField(max_length=120, blank=True, default="anonymous")
    prompt_tokens = IntegerField(default=0)
    completion_tokens = IntegerField(default=0)
    total_tokens = IntegerField(default=0)
    latency_ms = FloatField(default=0.0)
    status = CharField(max_length=32, default="ok")
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        table_name = "tblinc_token_usage"
        verbose_name = "Usage"
        verbose_name_plural = "Usage"


_TX_TYPE_CHOICES: list[tuple[str, str]] = [
    ("credit", "Credit / Top-Up"),
    ("bonus", "Welcome Bonus"),
    ("usage", "AI Usage Charge"),
    ("refund", "Refund / Adjustment"),
]

_TX_STATUS_CHOICES: list[tuple[str, str]] = [
    ("completed", "Completed"),
    ("pending", "Pending"),
    ("failed", "Failed"),
]


class BillingTransaction(Model):
    """Billing ledger recording user wallet top-ups, welcome bonuses, and per-inference USD charges."""

    username = CharField(max_length=120, verbose_name="User", placeholder="alice")
    tx_type = CharField(max_length=32, choices=_TX_TYPE_CHOICES, default="credit", verbose_name="Type")
    amount_usd = FloatField(default=0.0, verbose_name="Amount (USD)")
    balance_after_usd = FloatField(default=0.0, verbose_name="Balance After (USD)")
    tokens_added = IntegerField(default=0, verbose_name="Tokens Added")
    description = CharField(max_length=255, blank=True, default="", placeholder="Top-up $25.00 (+300,000 tokens)")
    reference_id = CharField(max_length=64, blank=True, default="", verbose_name="Reference ID")
    status = CharField(max_length=32, choices=_TX_STATUS_CHOICES, default="completed")
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        table_name = "tblinc_billing_transactions"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"

    def save(self, db: Any = None) -> BillingTransaction:
        if not str(self.reference_id or "").strip():
            self.reference_id = f"tx_{secrets.token_hex(6)}"
        is_new = self.pk is None
        if is_new and float(self.balance_after_usd or 0.0) == 0.0 and float(self.amount_usd or 0.0) != 0.0:
            try:
                from ..auth import User

                u = User.objects.get(username=str(self.username))
                new_bal = round(max(0.0, float(u.balance_usd or 0.0) + float(self.amount_usd)), 4)
                u.balance_usd = new_bal
                u.save()
                self.balance_after_usd = new_bal
            except Exception:
                pass
        return super().save(db=db)


def estimate_tokens(payload: Any, *, modality: str = "text") -> int:
    """Estimate realistic token count from text, JSON payloads, or media parameters."""
    if payload is None:
        return 8
    if isinstance(payload, str):
        text = payload
    else:
        try:
            text = json.dumps(payload, default=str)
        except TypeError:
            text = str(payload)
    # Strip huge base64 data URIs before char counting, then charge realistic media token weight
    media_bonus = 0
    if "data:image/" in text:
        media_bonus += 256
        text = text.split("data:image/")[0]
    if "data:audio/" in text:
        media_bonus += 180
        text = text.split("data:audio/")[0]
    if modality == "video":
        media_bonus += 320
    elif modality == "music":
        media_bonus += 200
    elif modality == "image":
        media_bonus += 160
    elif modality == "voice":
        media_bonus += 90

    base = max(4, math.ceil(len(text) / 4.0))
    return base + media_bonus


def extract_api_key_from_request(request: Request) -> str | None:
    """Extract an API key from `X-API-Key` or `Authorization: Bearer <key>` headers."""
    direct = request.header("X-API-Key")
    if direct and direct.strip():
        return direct.strip()
    auth = request.header("Authorization")
    if auth and auth.strip().lower().startswith("bearer "):
        tok = auth.strip()[7:].strip()
        if tok:
            return tok
    return None


def authenticate_api_key(request: Request, model_key: str | None = None) -> AIKey | None:
    """Validate an incoming tblinc API key header. Raises Http403 if an invalid/revoked/disallowed key is sent."""
    raw = extract_api_key_from_request(request)
    if not raw:
        return None
    try:
        key_obj = AIKey.objects.get(api_key=raw)
    except DoesNotExist as exc:
        raise Http403("Invalid AI API key.") from exc
    if not key_obj.is_active:
        raise Http403(f"AI API key '{key_obj.name}' has been revoked or disabled.")
    if model_key and not key_obj.allows_model(model_key):
        raise Http403(f"AI API key '{key_obj.name}' is not authorized for model '{model_key}'.")
    return key_obj


def ensure_default_quotas() -> None:
    """Seed the global '*' ModelQuota row if not already present."""
    try:
        if not ModelQuota.objects.filter(model_key="*").exists():
            ModelQuota.objects.create(
                model_key="*",
                token_limit=500_000,
                request_limit=5_000,
                tokens_used=0,
                requests_used=0,
                cost_per_1k_tokens=0.002,
                is_enabled=True,
            )
    except Exception:
        # Table may not be migrated yet in standalone unit tests
        pass


def _get_quota_row(key: str) -> ModelQuota | None:
    try:
        return ModelQuota.objects.get(model_key=key)
    except (DoesNotExist, Exception):
        return None


def check_quota(
    model_key: str,
    *,
    prompt_tokens: int,
    api_key_obj: AIKey | None = None,
    username: str = "anonymous",
) -> None:
    """Enforce Admin kill-switches, per-model quotas, global quota, and per-key quotas before inference."""
    ensure_default_quotas()
    canonical = registry.resolve_key(model_key)
    key_label = api_key_obj.name if api_key_obj else ("admin-session" if username != "anonymous" else "public-studio")

    # 1. Per-key quota check
    if api_key_obj is not None:
        t_lim = int(api_key_obj.token_quota or 0)
        r_lim = int(api_key_obj.request_quota or 0)
        if t_lim > 0 and (int(api_key_obj.tokens_used or 0) + prompt_tokens) > t_lim:
            _safe_log(canonical, key_label, username, prompt_tokens, 0, 0.0, "quota_exceeded")
            raise Http429(f"API key '{api_key_obj.name}' token quota exceeded ({api_key_obj.tokens_used}/{t_lim} tokens).")
        if r_lim > 0 and int(api_key_obj.requests_used or 0) >= r_lim:
            _safe_log(canonical, key_label, username, prompt_tokens, 0, 0.0, "quota_exceeded")
            raise Http429(f"API key '{api_key_obj.name}' request quota exceeded ({api_key_obj.requests_used}/{r_lim} requests).")

    # 2. Per-model and Global '*' quota checks
    for scope_key, label in ((canonical, f"Model '{canonical}'"), ("*", "Global AI")):
        row = _get_quota_row(scope_key)
        if row is None:
            continue
        if not row.is_enabled:
            _safe_log(canonical, key_label, username, prompt_tokens, 0, 0.0, "disabled")
            raise Http403(f"{label} is currently disabled by Admin quota policy.")
        t_lim = int(row.token_limit or 0)
        r_lim = int(row.request_limit or 0)
        if t_lim > 0 and (int(row.tokens_used or 0) + prompt_tokens) > t_lim:
            _safe_log(canonical, key_label, username, prompt_tokens, 0, 0.0, "quota_exceeded")
            raise Http429(f"{label} token quota exceeded ({row.tokens_used}/{t_lim} tokens).")
        if r_lim > 0 and int(row.requests_used or 0) >= r_lim:
            _safe_log(canonical, key_label, username, prompt_tokens, 0, 0.0, "quota_exceeded")
            raise Http429(f"{label} request quota exceeded ({row.requests_used}/{r_lim} requests).")


    # 3. User billing balance check (when user account exists and has billing history)
    if username and username not in {"anonymous", "api", "session"}:
        try:
            from ..auth import User

            u = User.objects.get(username=username)
            ensure_user_wallet(u.username)
            u = User.objects.get(username=username)
            if not u.is_superuser and float(u.balance_usd or 0.0) <= 0.0:
                _safe_log(canonical, key_label, username, prompt_tokens, 0, 0.0, "insufficient_balance")
                raise Http429(f"Insufficient billing balance (${float(u.balance_usd or 0.0):.2f}) for '{username}'. Top up at /billing/.")
        except Http429:
            raise
        except Exception:
            pass


def _safe_log(
    model_key: str,
    key_name: str,
    username: str,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    status: str,
) -> None:
    try:
        TokenUsageLog.objects.create(
            model_key=model_key,
            key_name=key_name,
            username=username,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=round(float(latency_ms), 2),
            status=status,
        )
    except Exception:
        pass


def record_token_usage(
    model_key: str,
    *,
    prompt_tokens: int,
    completion_tokens: int,
    latency_ms: float,
    api_key_obj: AIKey | None = None,
    username: str = "anonymous",
) -> dict[str, Any]:
    """Increment live token/request counters across AIKey, ModelQuota, TokenUsageLog, and User Billing Balance."""
    canonical = registry.resolve_key(model_key)
    total = int(prompt_tokens) + int(completion_tokens)
    key_label = api_key_obj.name if api_key_obj else ("admin-session" if username != "anonymous" else "public-studio")

    key_remaining: int | None = None
    if api_key_obj is not None:
        api_key_obj.tokens_used = int(api_key_obj.tokens_used or 0) + total
        api_key_obj.requests_used = int(api_key_obj.requests_used or 0) + 1
        api_key_obj.save()
        if int(api_key_obj.token_quota or 0) > 0:
            key_remaining = max(0, int(api_key_obj.token_quota) - int(api_key_obj.tokens_used))

    model_remaining: int | None = None
    cost_rate = 0.002
    for scope_key in (canonical, "*"):
        row = _get_quota_row(scope_key)
        if row is None:
            continue
        if scope_key == canonical and float(row.cost_per_1k_tokens or 0.0) > 0:
            cost_rate = float(row.cost_per_1k_tokens)
        elif scope_key == "*" and cost_rate == 0.002 and float(row.cost_per_1k_tokens or 0.0) > 0:
            cost_rate = float(row.cost_per_1k_tokens)
        row.tokens_used = int(row.tokens_used or 0) + total
        row.requests_used = int(row.requests_used or 0) + 1
        row.save()
        if scope_key == canonical and int(row.token_limit or 0) > 0:
            model_remaining = max(0, int(row.token_limit) - int(row.tokens_used))
        elif scope_key == "*" and model_remaining is None and int(row.token_limit or 0) > 0:
            model_remaining = max(0, int(row.token_limit) - int(row.tokens_used))

    _safe_log(canonical, key_label, username, prompt_tokens, completion_tokens, latency_ms, "ok")

    cost_usd = round(max(0.0001, (total / 1000.0) * cost_rate), 4)
    balance_usd: float | None = None
    if username and username not in {"anonymous", "api", "session"}:
        try:
            from ..auth import User

            ensure_user_wallet(username)
            u = User.objects.get(username=username)
            new_bal = round(max(0.0, float(u.balance_usd or 0.0) - cost_usd), 4)
            u.balance_usd = new_bal
            u.total_spent_usd = round(float(u.total_spent_usd or 0.0) + cost_usd, 4)
            u.save()
            balance_usd = new_bal
            BillingTransaction.objects.create(
                username=username,
                tx_type="usage",
                amount_usd=-cost_usd,
                balance_after_usd=new_bal,
                tokens_added=0,
                description=f"AI {canonical} inference ({total} tokens · {key_label})",
                status="completed",
            )
        except Exception:
            pass

    remaining = key_remaining if key_remaining is not None else model_remaining
    return {
        "model_key": canonical,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total,
        "cost_usd": cost_usd,
        "balance_usd": balance_usd,
        "quota_remaining": remaining,
        "key_name": key_label,
    }


def get_quota_overview() -> dict[str, Any]:
    """Return full Admin summary of API keys, all 25 model quotas, and recent token usage."""
    ensure_default_quotas()
    keys = [k.masked_dict() for k in AIKey.objects.order_by("-id").all()]
    quota_map = {q.model_key: q for q in ModelQuota.objects.all()}
    global_q = quota_map.get("*")

    model_rows: list[dict[str, Any]] = []
    if global_q is not None:
        t_lim = int(global_q.token_limit or 0)
        t_used = int(global_q.tokens_used or 0)
        model_rows.append(
            {
                "model_key": "*",
                "name": "Global Default (All Models)",
                "category": "Global",
                "token_limit": t_lim,
                "tokens_used": t_used,
                "token_pct": min(100, round((t_used / t_lim) * 100)) if t_lim > 0 else 0,
                "request_limit": int(global_q.request_limit or 0),
                "requests_used": int(global_q.requests_used or 0),
                "cost_usd": round((t_used / 1000.0) * float(global_q.cost_per_1k_tokens or 0.0), 4),
                "is_enabled": bool(global_q.is_enabled),
            }
        )

    enabled_count = 0
    for meta in list_models():
        k = meta["key"]
        q = quota_map.get(k)
        t_lim = int(q.token_limit or 0) if q else 0
        t_used = int(q.tokens_used or 0) if q else 0
        r_lim = int(q.request_limit or 0) if q else 0
        r_used = int(q.requests_used or 0) if q else 0
        cost = round((t_used / 1000.0) * float(q.cost_per_1k_tokens or 0.002), 4) if q else 0.0
        enabled = bool(q.is_enabled) if q else True
        if enabled:
            enabled_count += 1
        model_rows.append(
            {
                "model_key": k,
                "name": meta["name"],
                "category": meta["category"],
                "token_limit": t_lim,
                "tokens_used": t_used,
                "token_pct": min(100, round((t_used / t_lim) * 100)) if t_lim > 0 else 0,
                "request_limit": r_lim,
                "requests_used": r_used,
                "cost_usd": cost,
                "is_enabled": enabled,
            }
        )

    logs = [r.to_dict() for r in TokenUsageLog.objects.order_by("-id").limit(30).all()]
    total_tokens = int(global_q.tokens_used or 0) if global_q else sum(r["total_tokens"] for r in logs)
    total_requests = int(global_q.requests_used or 0) if global_q else len(logs)
    return {
        "summary": {
            "active_keys": sum(1 for k in keys if k["is_active"]),
            "total_keys": len(keys),
            "total_tokens_used": total_tokens,
            "global_token_limit": int(global_q.token_limit or 0) if global_q else 0,
            "total_requests": total_requests,
            "models_enabled": enabled_count,
            "total_models": len(list_models()),
        },
        "keys": keys,
        "quotas": model_rows,
        "recent_usage": logs,
    }


def provision_default_user_key(username: str) -> AIKey:
    """Create a starter personal tblinc AI key for a user if they do not have one yet."""
    existing = AIKey.objects.filter(owner_username=username).order_by("-id").all()
    if existing:
        return existing[0]
    key_obj = AIKey(
        name=f"{username} Starter AI Key",
        owner_username=username,
        provider="tblinc",
        allowed_models="*",
        token_quota=50_000,
        request_quota=500,
        is_active=True,
    )
    key_obj.save()
    return key_obj


def ensure_user_wallet(username: str) -> None:
    """Seed the initial $10.00 welcome credit transaction for a user if no billing records exist yet."""
    if not username or username in {"anonymous", "api", "session"}:
        return
    try:
        from ..auth import User

        user = User.objects.get(username=username)
        has_tx = BillingTransaction.objects.filter(username=username).exists()
        if not has_tx:
            bal = float(user.balance_usd if user.balance_usd is not None else 10.0)
            if bal <= 0.0 and float(user.total_spent_usd or 0.0) == 0.0:
                bal = 10.0
                user.balance_usd = 10.0
                user.save()
            BillingTransaction.objects.create(
                username=username,
                tx_type="bonus",
                amount_usd=round(bal, 4),
                balance_after_usd=round(bal, 4),
                tokens_added=50_000,
                description=f"Starter Welcome Credit (${bal:.2f} · 50,000 tokens)",
                status="completed",
            )
    except Exception:
        pass


def topup_user_balance(
    username: str,
    amount_usd: float,
    *,
    payment_method: str = "card",
    description: str = "",
) -> dict[str, Any]:
    """Credit a user's USD balance, upgrade their plan tier, boost active AI key quotas, and record a transaction."""
    from ..auth import User

    ensure_user_wallet(username)
    user = User.objects.get(username=username)
    amt = round(float(amount_usd), 2)
    if amt < 1.0 or amt > 10_000.0:
        raise ValueError("Top-up amount must be between $1.00 and $10,000.00.")

    # Determine bonus token quota ($1 = 10,000 tokens; Pro/Scale packages give bonus tokens)
    if amt >= 100.0:
        tokens_added = int(amt * 15_000)
        plan = "scale"
    elif amt >= 25.0:
        tokens_added = int(amt * 12_000)
        plan = "pro"
    else:
        tokens_added = int(amt * 10_000)
        plan = user.plan_tier if user.plan_tier in {"pro", "scale"} else "starter"

    reqs_added = max(100, tokens_added // 100)
    new_bal = round(float(user.balance_usd or 0.0) + amt, 4)
    user.balance_usd = new_bal
    user.plan_tier = plan
    user.save()

    # Boost active personal AI keys for this user
    user_keys = AIKey.objects.filter(owner_username=username).all()
    if not user_keys:
        user_keys = [provision_default_user_key(username)]
    for k in user_keys:
        if k.is_active and int(k.token_quota or 0) > 0:
            k.token_quota = int(k.token_quota) + tokens_added
        if k.is_active and int(k.request_quota or 0) > 0:
            k.request_quota = int(k.request_quota) + reqs_added
        k.save()

    desc = (description or "").strip() or f"Wallet Top-Up +${amt:.2f} via {payment_method} (+{tokens_added:,} tokens)"
    tx = BillingTransaction.objects.create(
        username=username,
        tx_type="credit",
        amount_usd=amt,
        balance_after_usd=new_bal,
        tokens_added=tokens_added,
        description=desc,
        status="completed",
    )
    return {
        "transaction": tx.to_dict(),
        "balance_usd": new_bal,
        "plan_tier": plan,
        "tokens_added": tokens_added,
    }


def get_user_billing_overview(username: str) -> dict[str, Any]:
    """Return user's current USD wallet balance, total spend, plan tier, and transaction ledger."""
    from ..auth import User

    ensure_user_wallet(username)
    try:
        user = User.objects.get(username=username)
        bal = round(float(user.balance_usd or 0.0), 4)
        spent = round(float(user.total_spent_usd or 0.0), 4)
        plan = str(user.plan_tier or "starter").upper()
    except Exception:
        bal, spent, plan = 10.0, 0.0, "STARTER"

    tx_objs = BillingTransaction.objects.filter(username=username).order_by("-id").limit(50).all()
    tx_list: list[dict[str, Any]] = []
    total_credited = 0.0
    for t in tx_objs:
        amt = float(t.amount_usd or 0.0)
        if amt > 0:
            total_credited += amt
        d = t.to_dict()
        d["is_credit"] = amt >= 0
        d["amount_display"] = f"+${amt:.2f}" if amt >= 0 else f"-${abs(amt):.4f}"
        d["balance_after_display"] = f"${float(t.balance_after_usd or 0.0):.4f}"
        tx_list.append(d)

    key_objs = AIKey.objects.filter(owner_username=username).all()
    tokens_used = sum(int(k.tokens_used or 0) for k in key_objs)
    total_quota = sum(int(k.token_quota or 0) for k in key_objs if k.is_active)
    remaining = max(0, total_quota - tokens_used) if total_quota > 0 else 0

    return {
        "balance_usd": bal,
        "balance_display": f"{bal:.2f}",
        "total_spent_usd": spent,
        "total_spent_display": f"{spent:.4f}",
        "total_credited_usd": round(total_credited, 2),
        "total_credited_display": f"{total_credited:.2f}",
        "plan_tier": plan,
        "tokens_used": tokens_used,
        "total_quota": total_quota,
        "tokens_remaining": remaining,
        "transaction_count": len(tx_list),
        "transactions": tx_list,
    }


def get_user_profile_overview(username: str) -> dict[str, Any]:
    """Return personal AI keys, token quota totals, billing summary, and recent usage logs for a signed-in user."""
    ensure_user_wallet(username)
    key_objs = AIKey.objects.filter(owner_username=username).order_by("-id").all()
    keys = [k.masked_dict() for k in key_objs]
    logs = [r.to_dict() for r in TokenUsageLog.objects.filter(username=username).order_by("-id").limit(25).all()]
    tokens_used = sum(int(k.tokens_used or 0) for k in key_objs)
    log_tokens = sum(int(r.get("total_tokens") or 0) for r in logs)
    total_tokens = max(tokens_used, log_tokens)
    total_requests = max(sum(int(k.requests_used or 0) for k in key_objs), len(logs))
    total_quota = sum(int(k.token_quota or 0) for k in key_objs if k.is_active)
    remaining = max(0, total_quota - tokens_used) if total_quota > 0 else 0
    billing = get_user_billing_overview(username)
    return {
        "summary": {
            "active_keys": sum(1 for k in keys if k["is_active"]),
            "total_keys": len(keys),
            "tokens_used": total_tokens,
            "total_quota": total_quota,
            "tokens_remaining": remaining,
            "total_requests": total_requests,
            "balance_usd": billing["balance_usd"],
            "balance_display": billing["balance_display"],
            "plan_tier": billing["plan_tier"],
        },
        "billing": billing,
        "keys": keys,
        "recent_usage": logs,
    }
