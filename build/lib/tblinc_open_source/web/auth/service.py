"""Built-in Authentication, PBKDF2 Password Hashing, Sessions, CSRF, and Auth Views."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from functools import wraps
from typing import Any, Callable
from urllib.parse import quote

from ..forms import CharFormField, EmailFormField, Form, PasswordFormField
from ..http import HtmlResponse, Http400, Http403, Http404, JsonResponse, RedirectResponse, Request, Response
from ..orm import BooleanField, CharField, DateTimeField, DoesNotExist, EmailField, FloatField, Model, PasswordField, TextField


def hash_password(raw_password: str, iterations: int = 200_000) -> str:
    """Hash a password with a per-user salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${dk.hex()}"


def verify_password(raw_password: str, encoded: str) -> bool:
    """Constant-time verification of a PBKDF2-HMAC-SHA256 hash."""
    try:
        algo, iters_s, salt, digest_hex = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt.encode("utf-8"), int(iters_s))
        return hmac.compare_digest(dk.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


class User(Model):
    """Built-in ORM User model with secure PBKDF2 password storage and USD billing balance."""

    username = CharField(max_length=120, unique=True)
    email = EmailField(max_length=255, blank=True, default="")
    password = PasswordField(max_length=255)
    balance_usd = FloatField(default=10.0, verbose_name="Balance (USD)")
    total_spent_usd = FloatField(default=0.0, verbose_name="Total Spent (USD)")
    plan_tier = CharField(max_length=32, default="starter", verbose_name="Plan Tier")
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        table_name = "tblinc_users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def set_password(self, raw_password: str) -> None:
        self.password = hash_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return verify_password(raw_password, self.password)

    def save(self, db: Any = None) -> User:
        if self.password and not str(self.password).startswith("pbkdf2_sha256$"):
            self.set_password(str(self.password))
        return super().save(db=db)


class Session(Model):
    """Server-side session record linked to signed HTTPOnly cookies."""

    session_key = CharField(max_length=128, unique=True)
    user_id = CharField(max_length=32, blank=True, default="")
    data_json = TextField(blank=True, default="{}")
    csrf_token = CharField(max_length=128)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        table_name = "tblinc_sessions"
        verbose_name = "Session"
        verbose_name_plural = "Sessions"


def create_user(
    username: str,
    password: str,
    email: str = "",
    *,
    is_staff: bool = False,
    is_superuser: bool = False,
) -> User:
    user = User(
        username=username,
        email=email,
        password=hash_password(password),
        is_active=True,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    user.save()
    return user


def create_superuser(username: str, password: str, email: str = "") -> User:
    try:
        existing = User.objects.get(username=username)
        existing.set_password(password)
        if email:
            existing.email = email
        existing.is_active = True
        existing.is_staff = True
        existing.is_superuser = True
        existing.save()
        return existing
    except DoesNotExist:
        return create_user(username, password, email=email, is_staff=True, is_superuser=True)


def purge_default_fake_admin() -> None:
    """Remove any legacy auto-seeded fake `admin / admin123` account from the database."""
    try:
        u = User.objects.get(username="admin")
        if u.check_password("admin123"):
            u.delete()
    except Exception:
        pass


def authenticate(username: str, password: str) -> User | None:
    if username == "admin" and password == "admin123":
        purge_default_fake_admin()
        return None
    try:
        user = User.objects.get(username=username)
    except DoesNotExist:
        return None
    if user.username == "admin" and user.check_password("admin123"):
        user.delete()
        return None
    if user.is_active and user.check_password(password):
        return user
    return None


def _sign_value(value: str, secret_key: str) -> str:
    sig = hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return f"{value}.{sig}"


def _unsign_value(signed: str, secret_key: str) -> str | None:
    if "." not in signed:
        return None
    val, sig = signed.rsplit(".", 1)
    expected = hmac.new(secret_key.encode("utf-8"), val.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    return val if hmac.compare_digest(sig, expected) else None


def login(request: Request, user: User) -> None:
    """Attach authenticated user to the current session."""
    request.user = user
    request.session["user_id"] = str(user.pk)
    if request.session_key:
        try:
            sess = Session.objects.get(session_key=request.session_key)
            sess.user_id = str(user.pk)
            sess.save()
        except DoesNotExist:
            pass


def logout(request: Request) -> None:
    """Clear authenticated user from the current session."""
    request.user = None
    request.session.pop("user_id", None)
    if request.session_key:
        try:
            sess = Session.objects.get(session_key=request.session_key)
            sess.user_id = ""
            sess.save()
        except DoesNotExist:
            pass


def session_and_auth_middleware(request: Request, call_next: Callable[[Request], Response]) -> Response:
    """Loads/creates signed server-side sessions, populates request.user, and enforces CSRF."""
    secret = getattr(request.app, "secret_key", "tblinc-dev-secret")
    cookie_name = "tblinc_session"
    signed = request.cookies.get(cookie_name, "")
    skey = _unsign_value(signed, secret) if signed else None

    session_obj: Session | None = None
    if skey:
        try:
            session_obj = Session.objects.get(session_key=skey)
        except DoesNotExist:
            session_obj = None

    created = False
    if session_obj is None:
        skey = secrets.token_urlsafe(32)
        session_obj = Session(session_key=skey, user_id="", data_json="{}", csrf_token=secrets.token_hex(24))
        session_obj.save()
        created = True

    request.session_key = session_obj.session_key
    request.csrf_token = session_obj.csrf_token
    if session_obj.user_id:
        try:
            request.user = User.objects.get(id=int(session_obj.user_id))
        except (DoesNotExist, ValueError):
            request.user = None

    # Enforce CSRF on browser form mutations (JSON API calls may send X-CSRF-Token or opt in via API)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and not request.is_json:
        csrf_exempt = getattr(request.app, "csrf_exempt_prefixes", ("/api/",))
        if not any(request.path.startswith(pref) for pref in csrf_exempt):
            submitted = request.POST.get("csrf_token") or request.header("X-CSRF-Token")
            if not submitted or not hmac.compare_digest(str(submitted), str(request.csrf_token)):
                raise Http403("CSRF verification failed. Missing or invalid CSRF token.")

    response = call_next(request)
    if created:
        response.set_cookie(cookie_name, _sign_value(session_obj.session_key, secret), httponly=True, samesite="Lax")
    return response


def login_required(login_url: str = "/auth/login/") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(view_fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view_fn)
        def wrapped(request: Request, *args: Any, **kwargs: Any) -> Any:
            if request.user is None:
                return RedirectResponse(f"{login_url}?next={quote(request.full_path)}")
            return view_fn(request, *args, **kwargs)

        return wrapped

    return decorator


def staff_required(login_url: str = "/admin/login/") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(view_fn: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(view_fn)
        def wrapped(request: Request, *args: Any, **kwargs: Any) -> Any:
            if request.user is None or not (request.user.is_staff or request.user.is_superuser):
                return RedirectResponse(f"{login_url}?next={quote(request.full_path)}")
            return view_fn(request, *args, **kwargs)

        return wrapped

    return decorator


class LoginForm(Form):
    username = CharFormField(label="Username", placeholder="username")
    password = PasswordFormField(label="Password", placeholder="••••••••")


class RegisterForm(Form):
    username = CharFormField(label="Username", min_length=3, placeholder="developer")
    email = EmailFormField(label="Email", placeholder="dev@example.com")
    password = PasswordFormField(label="Password", min_length=6, placeholder="Create a strong password")


def register_auth_routes(app: Any, prefix: str = "/auth") -> None:
    """Mount login, sign-up, logout, user profile, workspace settings, and personal AI key routes onto a TblincApp."""

    @app.route(f"{prefix}/login/", methods=("GET", "POST"), name="auth:login")
    def login_view(request: Request) -> Response:
        next_url = request.GET.get("next") or request.POST.get("next") or "/profile/"
        form = LoginForm(request.POST if request.method == "POST" else None)
        if request.method == "POST" and form.is_valid():
            user = authenticate(form.cleaned_data["username"], form.cleaned_data["password"])
            if user is not None:
                login(request, user)
                return RedirectResponse(next_url)
            form.errors["__all__"] = "Invalid username or password."
        reg_url = f"{prefix}/register/?next={quote(next_url)}" if next_url != "/profile/" else f"{prefix}/register/"
        return app.render(
            request,
            "tblinc_auth.html",
            {
                "auth_mode": "login",
                "title": "Sign In",
                "subtitle": "Sign in to access your profile, personal AI keys, and workspace.",
                "button_label": "Sign In",
                "form_html": form.as_html(),
                "next_url": next_url,
                "login_url": f"{prefix}/login/",
                "register_url": reg_url,
                "alt_text": "Need an account?",
                "alt_label": "Sign Up",
                "alt_url": reg_url,
            },
        )

    @app.route(f"{prefix}/register/", methods=("GET", "POST"), name="auth:register")
    def register_view(request: Request) -> Response:
        try:
            from ..admin.settings_store import get_app_settings

            if not get_app_settings(app=app).get("allow_registration_bool", True):
                raise Http403("User registration is currently disabled in Admin Settings.")
        except Http403:
            raise
        except Exception:
            pass
        next_url = request.GET.get("next") or request.POST.get("next") or "/profile/?welcome=1"
        form = RegisterForm(request.POST if request.method == "POST" else None)
        if request.method == "POST" and form.is_valid():
            if User.objects.filter(username=form.cleaned_data["username"]).exists():
                form.errors["username"] = "That username is already taken."
            else:
                user = create_user(
                    username=form.cleaned_data["username"],
                    password=form.cleaned_data["password"],
                    email=form.cleaned_data["email"],
                )
                try:
                    from ..admin.quota import ensure_user_wallet, provision_default_user_key

                    provision_default_user_key(user.username)
                    ensure_user_wallet(user.username)
                except Exception:
                    pass
                login(request, user)
                return RedirectResponse(next_url)
        login_url = f"{prefix}/login/?next={quote(next_url)}" if next_url != "/profile/?welcome=1" else f"{prefix}/login/"
        return app.render(
            request,
            "tblinc_auth.html",
            {
                "auth_mode": "register",
                "title": "Create Account",
                "subtitle": "Sign up to get your user profile and personal tblinc AI API key.",
                "button_label": "Sign Up",
                "form_html": form.as_html(),
                "next_url": next_url,
                "login_url": login_url,
                "register_url": f"{prefix}/register/",
                "alt_text": "Already have an account?",
                "alt_label": "Sign In",
                "alt_url": login_url,
            },
        )

    @app.route(f"{prefix}/logout/", methods=("GET", "POST"), name="auth:logout")
    def logout_view(request: Request) -> Response:
        logout(request)
        return RedirectResponse("/")

    @app.route("/profile/", methods=("GET",), name="user:profile")
    @login_required(login_url=f"{prefix}/login/")
    def user_profile_view(request: Request) -> Response:
        from ...ai_models import list_models
        from ..admin.quota import ensure_user_wallet, get_user_profile_overview, provision_default_user_key

        assert request.user is not None
        try:
            provision_default_user_key(request.user.username)
            ensure_user_wallet(request.user.username)
        except Exception:
            pass
        overview = get_user_profile_overview(request.user.username)
        return app.render(
            request,
            "tblinc_profile.html",
            {
                "active_nav": "profile",
                "profile_user": request.user,
                "user_initials": (request.user.username[:2] or "U").upper(),
                "summary": overview["summary"],
                "billing": overview["billing"],
                "user_keys": overview["keys"],
                "recent_usage": overview["recent_usage"],
                "ai_models": list_models(),
                "welcome": bool(request.GET.get("welcome")),
                "flash_msg": request.GET.get("msg", ""),
                "flash_err": request.GET.get("err", ""),
            },
        )

    @app.route("/billing/", methods=("GET",), name="user:billing")
    @login_required(login_url=f"{prefix}/login/")
    def user_billing_view(request: Request) -> Response:
        from ..admin.quota import ensure_user_wallet, get_user_billing_overview, provision_default_user_key

        assert request.user is not None
        try:
            provision_default_user_key(request.user.username)
            ensure_user_wallet(request.user.username)
        except Exception:
            pass
        billing = get_user_billing_overview(request.user.username)
        return app.render(
            request,
            "tblinc_billing.html",
            {
                "active_nav": "billing",
                "profile_user": request.user,
                "billing": billing,
                "transactions": billing["transactions"],
            },
        )

    @app.route("/profile/update/", methods=("POST",), name="user:profile_update")
    @login_required(login_url=f"{prefix}/login/")
    def user_profile_update(request: Request) -> Response:
        assert request.user is not None
        email = str(request.POST.get("email", "")).strip()
        if email and ("@" not in email or "." not in email.split("@")[-1]):
            return RedirectResponse("/profile/?err=" + quote("Please enter a valid email address."))
        request.user.email = email
        request.user.save()
        return RedirectResponse("/profile/?msg=" + quote("Profile updated successfully."))

    @app.route("/profile/password/", methods=("POST",), name="user:profile_password")
    @login_required(login_url=f"{prefix}/login/")
    def user_profile_password(request: Request) -> Response:
        assert request.user is not None
        current_pw = str(request.POST.get("current_password", ""))
        new_pw = str(request.POST.get("new_password", ""))
        confirm_pw = str(request.POST.get("confirm_password", ""))
        if not request.user.check_password(current_pw):
            return RedirectResponse("/profile/?err=" + quote("Current password is incorrect."))
        if len(new_pw) < 6:
            return RedirectResponse("/profile/?err=" + quote("New password must be at least 6 characters."))
        if new_pw != confirm_pw:
            return RedirectResponse("/profile/?err=" + quote("New passwords do not match."))
        request.user.set_password(new_pw)
        request.user.save()
        return RedirectResponse("/profile/?msg=" + quote("Password updated successfully."))

    @app.route("/settings/", methods=("GET",), name="user:settings")
    def user_settings_view(request: Request) -> Response:
        from ...ai_models import detect_hardware, list_models
        from ..admin.quota import get_user_profile_overview

        user_keys: list[dict[str, Any]] = []
        if request.user is not None:
            user_keys = get_user_profile_overview(request.user.username)["keys"]
        return app.render(
            request,
            "tblinc_settings.html",
            {
                "active_nav": "settings",
                "user_keys": user_keys,
                "ai_count": len(list_models()),
                "hardware": detect_hardware(),
            },
        )

    def _require_logged_in_api(request: Request) -> User:
        if request.user is None:
            raise Http403("Please sign in (/auth/login/) to manage your personal AI keys.")
        return request.user

    def _get_owned_key(user: User, key_id: int) -> Any:
        from ..admin.quota import AIKey

        try:
            key_obj = AIKey.objects.get(id=key_id)
        except DoesNotExist as exc:
            raise Http404(f"AI key #{key_id} not found.") from exc
        if key_obj.owner_username != user.username and not (user.is_staff or user.is_superuser):
            raise Http403("You do not have permission to manage this AI key.")
        return key_obj

    @app.route("/api/user/keys", methods=("GET", "POST"), name="api:user_keys")
    def api_user_keys(request: Request) -> Response:
        from ..admin.quota import AIKey, get_user_profile_overview

        user = _require_logged_in_api(request)
        if request.method == "GET":
            return JsonResponse({"ok": True, **get_user_profile_overview(user.username)})

        existing = AIKey.objects.filter(owner_username=user.username).all()
        if not (user.is_staff or user.is_superuser) and len(existing) >= 10:
            raise Http400("Maximum of 10 personal AI keys reached. Delete an unused key first.")

        payload = request.json() if request.body else {}
        name = str(payload.get("name", "")).strip() or f"{user.username} AI Key"
        allowed = str(payload.get("allowed_models", "*")).strip() or "*"
        try:
            req_tokens = int(payload.get("token_quota", 50_000))
            req_calls = int(payload.get("request_quota", 500))
        except (TypeError, ValueError) as exc:
            raise Http400("token_quota and request_quota must be integers.") from exc

        if not (user.is_staff or user.is_superuser):
            token_quota = max(1_000, min(req_tokens if req_tokens > 0 else 50_000, 100_000))
            request_quota = max(10, min(req_calls if req_calls > 0 else 500, 1_000))
        else:
            token_quota = max(0, req_tokens)
            request_quota = max(0, req_calls)

        key_obj = AIKey(
            name=name,
            owner_username=user.username,
            provider="tblinc",
            allowed_models=allowed,
            token_quota=token_quota,
            request_quota=request_quota,
            is_active=True,
        )
        key_obj.save()
        data = key_obj.masked_dict()
        data["api_key"] = key_obj.api_key
        return JsonResponse({"ok": True, "key": data}, status=201)

    @app.route("/api/user/keys/<int:key_id>/reveal", methods=("POST",), name="api:user_key_reveal")
    def api_user_key_reveal(request: Request, key_id: int) -> Response:
        user = _require_logged_in_api(request)
        key_obj = _get_owned_key(user, key_id)
        return JsonResponse({"ok": True, "id": key_obj.pk, "name": key_obj.name, "api_key": key_obj.api_key})

    @app.route("/api/user/keys/<int:key_id>/toggle", methods=("POST",), name="api:user_key_toggle")
    def api_user_key_toggle(request: Request, key_id: int) -> Response:
        user = _require_logged_in_api(request)
        key_obj = _get_owned_key(user, key_id)
        key_obj.is_active = not bool(key_obj.is_active)
        key_obj.save()
        return JsonResponse({"ok": True, "key": key_obj.masked_dict()})

    @app.route("/api/user/keys/<int:key_id>/rotate", methods=("POST",), name="api:user_key_rotate")
    def api_user_key_rotate(request: Request, key_id: int) -> Response:
        from ..admin.quota import generate_tblinc_key

        user = _require_logged_in_api(request)
        key_obj = _get_owned_key(user, key_id)
        key_obj.api_key = generate_tblinc_key()
        key_obj.save()
        data = key_obj.masked_dict()
        data["api_key"] = key_obj.api_key
        return JsonResponse({"ok": True, "key": data})

    @app.route("/api/user/keys/<int:key_id>", methods=("DELETE",), name="api:user_key_delete")
    def api_user_key_delete(request: Request, key_id: int) -> Response:
        user = _require_logged_in_api(request)
        key_obj = _get_owned_key(user, key_id)
        key_obj.delete()
        return JsonResponse({"ok": True, "deleted": key_id})

    @app.route("/api/user/billing", methods=("GET",), name="api:user_billing")
    def api_user_billing(request: Request) -> Response:
        from ..admin.quota import get_user_billing_overview

        user = _require_logged_in_api(request)
        return JsonResponse({"ok": True, **get_user_billing_overview(user.username)})

    @app.route("/api/user/billing/topup", methods=("POST",), name="api:user_billing_topup")
    def api_user_billing_topup(request: Request) -> Response:
        from ..admin.quota import topup_user_balance

        user = _require_logged_in_api(request)
        payload = request.json() if request.body else {}
        try:
            amount = float(payload.get("amount_usd", 25.0))
        except (TypeError, ValueError) as exc:
            raise Http400("amount_usd must be a valid number.") from exc
        method = str(payload.get("payment_method", "card")).strip() or "card"
        desc = str(payload.get("description", "")).strip()
        try:
            result = topup_user_balance(user.username, amount, payment_method=method, description=desc)
        except ValueError as exc:
            raise Http400(str(exc)) from exc
        return JsonResponse({"ok": True, **result}, status=201)
