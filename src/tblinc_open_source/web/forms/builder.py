"""Declarative Forms and ModelForms with validation and Tailwind CSS rendering."""

from __future__ import annotations

import html
import json
from typing import Any

from ..orm import (
    BooleanField as ORMBooleanField,
    FloatField as ORMFloatField,
    IntegerField as ORMIntegerField,
    JSONField as ORMJSONField,
    Model,
    PasswordField as ORMPasswordField,
    TextField as ORMTextField,
    ValidationError,
)
from ..templates import SafeString, mark_safe

_INPUT_CLS = (
    "w-full rounded-xl bg-white dark:bg-slate-900/80 border border-slate-300 dark:border-slate-700/80 "
    "px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 "
    "focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition shadow-sm"
)


_DEFAULT_SOURCE_URI_SUGGESTIONS: list[str] = [
    "local://knowledge_base",
    "local://datasets/images.json",
    "local://datasets/text_corpus.json",
    "local://datasets/audio_clips.json",
    "local://datasets/video_frames.json",
    "local://datasets/tabular.csv",
    "file:///path/to/dataset.json",
    "https://huggingface.co/datasets/",
    "s3://my-bucket/datasets/",
]


class FormField:
    """Base HTML form field with coercion, validation, and Tailwind widget rendering."""

    widget: str = "text"

    def __init__(
        self,
        *,
        label: str | None = None,
        required: bool = True,
        initial: Any = "",
        placeholder: str = "",
        help_text: str = "",
        choices: list[tuple[Any, str]] | None = None,
        suggestions: list[str] | None = None,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        self.name: str = ""
        self.label = label
        self.required = required
        self.initial = initial
        self.placeholder = placeholder
        self.help_text = help_text
        self.choices = choices
        self.suggestions = list(suggestions) if suggestions else None
        self.min_length = min_length
        self.max_length = max_length

    @property
    def display_label(self) -> str:
        return self.label or self.name.replace("_", " ").title()

    def clean(self, raw_value: Any) -> Any:
        text = "" if raw_value is None else str(raw_value).strip()
        if not text:
            if self.required:
                raise ValueError(f"{self.display_label} is required.")
            return ""
        if self.min_length is not None and len(text) < self.min_length:
            raise ValueError(f"{self.display_label} must be at least {self.min_length} characters.")
        if self.max_length is not None and len(text) > self.max_length:
            raise ValueError(f"{self.display_label} must be at most {self.max_length} characters.")
        return text

    def render_widget(self, value: Any) -> str:
        esc_name = html.escape(self.name, quote=True)
        esc_val = html.escape("" if value is None else str(value), quote=True)
        esc_ph = html.escape(self.placeholder, quote=True)

        if self.choices:
            opts = []
            for cval, clabel in self.choices:
                sel = " selected" if str(cval) == str(value) else ""
                opts.append(f'<option value="{html.escape(str(cval), quote=True)}"{sel}>{html.escape(str(clabel))}</option>')
            return f'<select id="id_{esc_name}" name="{esc_name}" class="{_INPUT_CLS}">{"".join(opts)}</select>'

        if self.widget == "textarea":
            return (
                f'<textarea id="id_{esc_name}" name="{esc_name}" rows="4" '
                f'placeholder="{esc_ph}" class="{_INPUT_CLS}">{esc_val}</textarea>'
            )

        if self.widget == "checkbox":
            checked = " checked" if str(value).lower() in {"1", "true", "yes", "on"} or value is True else ""
            return (
                f'<label class="inline-flex items-center gap-2.5 cursor-pointer">'
                f'<input id="id_{esc_name}" name="{esc_name}" type="checkbox" value="1"{checked} '
                f'class="h-4 w-4 rounded border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900 '
                f'text-indigo-600 focus:ring-indigo-500">'
                f'<span class="text-sm text-slate-700 dark:text-slate-300">Enabled</span></label>'
            )

        req = " required" if self.required and self.widget != "password" else ""
        step = ' step="any"' if self.widget == "number" else ""
        list_attr = ""
        datalist_html = ""
        if self.suggestions:
            dl_id = f"list_{esc_name}"
            list_attr = f' list="{dl_id}"'
            dl_opts = "".join(f'<option value="{html.escape(str(s), quote=True)}"></option>' for s in self.suggestions)
            datalist_html = f'<datalist id="{dl_id}">{dl_opts}</datalist>'
        return (
            f'<input id="id_{esc_name}" name="{esc_name}" type="{self.widget}" '
            f'value="{esc_val}" placeholder="{esc_ph}"{list_attr}{step}{req} class="{_INPUT_CLS}">{datalist_html}'
        )


class CharFormField(FormField):
    widget = "text"


class EmailFormField(FormField):
    widget = "email"

    def clean(self, raw_value: Any) -> str:
        val = super().clean(raw_value)
        if val and ("@" not in val or "." not in val.split("@")[-1]):
            raise ValueError("Enter a valid email address.")
        return val


class PasswordFormField(FormField):
    widget = "password"


class TextAreaFormField(FormField):
    widget = "textarea"


class IntegerFormField(FormField):
    widget = "number"

    def clean(self, raw_value: Any) -> int | None:
        val = super().clean(raw_value)
        if val == "":
            return None
        try:
            return int(val)
        except ValueError as exc:
            raise ValueError(f"{self.display_label} must be an integer.") from exc


class FloatFormField(FormField):
    widget = "number"

    def clean(self, raw_value: Any) -> float | None:
        val = super().clean(raw_value)
        if val == "":
            return None
        try:
            return float(val)
        except ValueError as exc:
            raise ValueError(f"{self.display_label} must be a number.") from exc


class BooleanFormField(FormField):
    widget = "checkbox"

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("required", False)
        super().__init__(**kwargs)

    def clean(self, raw_value: Any) -> bool:
        if isinstance(raw_value, bool):
            return raw_value
        return str(raw_value or "").lower() in {"1", "true", "yes", "on"}


class JSONFormField(FormField):
    widget = "textarea"

    def clean(self, raw_value: Any) -> Any:
        if raw_value is None or str(raw_value).strip() == "":
            return {}
        if not isinstance(raw_value, str):
            return raw_value
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON: {exc}") from exc


class FormMeta(type):
    def __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, Any]) -> type:
        declared: dict[str, FormField] = {}
        for base in reversed(bases):
            if hasattr(base, "_declared_fields"):
                declared.update(base._declared_fields)
        for attr, val in list(namespace.items()):
            if isinstance(val, FormField):
                val.name = attr
                declared[attr] = val
                del namespace[attr]
        namespace["_declared_fields"] = declared
        return super().__new__(mcs, name, bases, namespace)


class Form(metaclass=FormMeta):
    """Base Form supporting POST data binding, validation, errors, and Tailwind rendering."""

    _declared_fields: dict[str, FormField]

    def __init__(self, data: dict[str, Any] | None = None, initial: dict[str, Any] | None = None) -> None:
        self.data = data
        self.is_bound = data is not None
        self.initial = dict(initial or {})
        self.fields: dict[str, FormField] = dict(self._declared_fields)
        self.cleaned_data: dict[str, Any] = {}
        self.errors: dict[str, str] = {}

    def is_valid(self) -> bool:
        if not self.is_bound:
            return False
        self.cleaned_data = {}
        self.errors = {}
        for fname, field in self.fields.items():
            raw = self.data.get(fname) if self.data is not None else None
            try:
                self.cleaned_data[fname] = field.clean(raw)
            except ValueError as exc:
                self.errors[fname] = str(exc)
        if not self.errors:
            try:
                self.clean()
            except ValueError as exc:
                self.errors["__all__"] = str(exc)
        return not self.errors

    def clean(self) -> None:
        """Override for cross-field validation."""

    def value_for(self, fname: str) -> Any:
        if self.is_bound and self.data is not None and fname in self.data:
            return self.data[fname]
        if fname in self.initial:
            val = self.initial[fname]
            if isinstance(val, (dict, list)):
                return json.dumps(val, indent=2)
            return val
        return self.fields[fname].initial

    def as_html(self) -> SafeString:
        blocks: list[str] = []
        if "__all__" in self.errors:
            blocks.append(
                '<div class="rounded-xl border border-rose-300 dark:border-rose-500/40 '
                'bg-rose-50 dark:bg-rose-500/10 px-4 py-3 text-sm text-rose-700 dark:text-rose-200">'
                f"{html.escape(self.errors['__all__'])}</div>"
            )
        for fname, field in self.fields.items():
            val = "" if field.widget == "password" else self.value_for(fname)
            err = self.errors.get(fname)
            err_html = (
                f'<p class="mt-1.5 text-xs text-rose-600 dark:text-rose-400">{html.escape(err)}</p>' if err else ""
            )
            help_html = (
                f'<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{html.escape(field.help_text)}</p>'
                if field.help_text
                else ""
            )
            req_mark = ' <span class="text-indigo-500 dark:text-indigo-400">*</span>' if field.required else ""
            blocks.append(
                f'<div class="space-y-1.5">'
                f'<label for="id_{html.escape(fname, quote=True)}" '
                f'class="block text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-300">'
                f"{html.escape(field.display_label)}{req_mark}</label>"
                f"{field.render_widget(val)}{help_html}{err_html}</div>"
            )
        return mark_safe("\n".join(blocks))


def _orm_field_to_form_field(orm_field: Any) -> FormField:
    placeholder = getattr(orm_field, "placeholder", "") or ""
    help_text = orm_field.help_text
    suggestions = getattr(orm_field, "suggestions", None)
    initial = orm_field.get_default() if not callable(orm_field.default) else ""

    if orm_field.name == "model_key" and initial and orm_field.choices:
        valid_keys = {c[0] for c in orm_field.choices}
        if initial not in valid_keys:
            try:
                from ...ai_models import registry

                resolved = registry.resolve_key(str(initial))
                if resolved in valid_keys:
                    initial = resolved
            except Exception:
                pass

    if orm_field.name == "source_uri":
        placeholder = placeholder or "local://datasets/train.json or https://..."
        help_text = help_text or "Dataset path or URL (local://, file://, https://, hf://, or s3://)."
        suggestions = suggestions or _DEFAULT_SOURCE_URI_SUGGESTIONS
        if not initial:
            initial = "local://datasets/custom.json"

    common = {
        "label": orm_field.label,
        "required": not (orm_field.nullable or orm_field.blank or isinstance(orm_field, ORMBooleanField)),
        "initial": initial,
        "placeholder": placeholder,
        "help_text": help_text,
        "choices": orm_field.choices,
        "suggestions": suggestions,
    }
    if isinstance(orm_field, ORMBooleanField):
        ff: FormField = BooleanFormField(**common)
    elif isinstance(orm_field, ORMIntegerField):
        ff = IntegerFormField(**common)
    elif isinstance(orm_field, ORMFloatField):
        ff = FloatFormField(**common)
    elif isinstance(orm_field, ORMJSONField):
        ff = JSONFormField(**common)
    elif isinstance(orm_field, ORMPasswordField):
        ff = PasswordFormField(**common)
    elif isinstance(orm_field, ORMTextField):
        ff = TextAreaFormField(**common)
    elif orm_field.input_type == "email":
        ff = EmailFormField(**common)
    else:
        ff = CharFormField(**common)
    ff.name = orm_field.name
    return ff


class ModelForm(Form):
    """Automatically generates validated HTML forms from any tblinc ORM Model."""

    model: type[Model]
    exclude: tuple[str, ...] = ()

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        instance: Model | None = None,
        *,
        model: type[Model] | None = None,
        exclude: tuple[str, ...] | None = None,
    ) -> None:
        if model is not None:
            self.model = model
        self.instance = instance
        skip = set(exclude if exclude is not None else self.exclude)
        initial: dict[str, Any] = {}
        generated: dict[str, FormField] = {}

        for fname, orm_field in self.model._fields.items():
            if orm_field.primary_key or not orm_field.editable or fname in skip:
                continue
            ff = _orm_field_to_form_field(orm_field)
            if instance is not None and isinstance(orm_field, ORMPasswordField):
                ff.required = False
                ff.help_text = ff.help_text or "Leave blank to keep existing password."

            if self.model.__name__ != "User" and fname in {"username", "owner_username"}:
                try:
                    from ..auth import User

                    users = User.objects.order_by("username").all()
                    user_choices: list[tuple[Any, str]] = []
                    if not ff.required:
                        user_choices.append(("", "admin — System / Default"))
                    seen_usernames: set[str] = {c[0] for c in user_choices}
                    for u in users:
                        uname = str(u.username)
                        if uname in seen_usernames:
                            continue
                        seen_usernames.add(uname)
                        bal = float(getattr(u, "balance_usd", 0.0) or 0.0)
                        role = "Admin" if (u.is_staff or u.is_superuser) else "User"
                        email_part = f" · {u.email}" if u.email else ""
                        user_choices.append((uname, f"{uname} ({role}{email_part} · ${bal:.2f})"))
                    cur_val = str(getattr(instance, fname, "") or "") if instance is not None else ""
                    if cur_val and cur_val not in seen_usernames:
                        user_choices.append((cur_val, f"{cur_val}"))
                        seen_usernames.add(cur_val)
                    post_val = str(data.get(fname, "") or "") if data is not None else ""
                    if post_val and post_val not in seen_usernames:
                        user_choices.append((post_val, f"{post_val}"))
                        seen_usernames.add(post_val)
                    if not user_choices:
                        user_choices.append(("admin", "admin"))
                    ff.choices = user_choices
                    if not initial.get(fname) and instance is None and user_choices:
                        ff.initial = user_choices[0][0]
                except Exception:
                    pass

            generated[fname] = ff
            if instance is not None:
                initial[fname] = getattr(instance, fname, "")

        super().__init__(data=data, initial=initial)
        # Preserve any manually declared field overrides
        self.fields = {**generated, **self._declared_fields}

    def save(self, commit: bool = True) -> Model:
        if not self.cleaned_data and not self.is_valid():
            raise ValidationError(self.errors)
        obj = self.instance if self.instance is not None else self.model()
        for fname, val in self.cleaned_data.items():
            orm_field = self.model._fields.get(fname)
            if isinstance(orm_field, ORMPasswordField) and not val and self.instance is not None:
                continue
            setattr(obj, fname, val)
        if commit:
            obj.save()
        return obj
