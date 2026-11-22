"""Typed URL Router with named reverse lookup, route groups, and MVC/MTV dispatch."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from ..http import HttpError

_PARAM_RE = re.compile(r"<(?:(?P<conv>int|str|float|path):)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>")

_CONVERTERS: dict[str, tuple[str, Callable[[str], Any]]] = {
    "int": (r"\d+", int),
    "float": (r"\d+(?:\.\d+)?", float),
    "str": (r"[^/]+", str),
    "path": (r".+", str),
}


def _compile_pattern(pattern: str) -> tuple[re.Pattern[str], dict[str, Callable[[str], Any]]]:
    normalized = "/" + pattern.strip("/")
    if pattern.endswith("/") and normalized != "/":
        normalized += "/"

    regex_parts: list[str] = ["^"]
    converters: dict[str, Callable[[str], Any]] = {}
    pos = 0
    for match in _PARAM_RE.finditer(normalized):
        regex_parts.append(re.escape(normalized[pos : match.start()]))
        conv_name = match.group("conv") or "str"
        param_name = match.group("name")
        pat, conv_fn = _CONVERTERS[conv_name]
        converters[param_name] = conv_fn
        regex_parts.append(f"(?P<{param_name}>{pat})")
        pos = match.end()
    regex_parts.append(re.escape(normalized[pos:]))

    # Match with or without trailing slash for ergonomic URL handling
    if normalized != "/":
        if regex_parts[-1].endswith(r"\/"):
            regex_parts[-1] = regex_parts[-1][:-2] + "/?"
        else:
            regex_parts.append("/?")
    regex_parts.append("$")
    return re.compile("".join(regex_parts)), converters


@dataclass
class Route:
    pattern: str
    handler: Callable[..., Any]
    methods: tuple[str, ...]
    name: str | None
    regex: re.Pattern[str]
    converters: dict[str, Callable[[str], Any]]

    def match(self, path: str) -> dict[str, Any] | None:
        m = self.regex.match(path)
        if not m:
            return None
        params: dict[str, Any] = {}
        for key, raw_val in m.groupdict().items():
            params[key] = self.converters[key](raw_val)
        return params

    def build_url(self, **params: Any) -> str:
        def repl(match: re.Match[str]) -> str:
            pname = match.group("name")
            if pname not in params:
                raise KeyError(f"Missing URL parameter '{pname}' for route '{self.name or self.pattern}'")
            return str(params[pname])

        return _PARAM_RE.sub(repl, self.pattern)


class Router:
    """High-level URL router supporting decorators, path() helpers, and include() mounting."""

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix.rstrip("/")
        self.routes: list[Route] = []
        self._named: dict[str, Route] = {}

    def _join(self, pattern: str) -> str:
        if not self.prefix:
            return pattern if pattern.startswith("/") else "/" + pattern
        tail = pattern.lstrip("/")
        return f"{self.prefix}/{tail}" if tail else f"{self.prefix}/"

    def add(
        self,
        pattern: str,
        handler: Callable[..., Any],
        *,
        methods: tuple[str, ...] | list[str] = ("GET",),
        name: str | None = None,
    ) -> Route:
        full_pat = self._join(pattern)
        norm_methods = tuple(m.upper() for m in methods)
        regex, converters = _compile_pattern(full_pat)
        route = Route(
            pattern=full_pat,
            handler=handler,
            methods=norm_methods,
            name=name,
            regex=regex,
            converters=converters,
        )
        self.routes.append(route)
        if name:
            self._named[name] = route
        return route

    def route(
        self,
        pattern: str,
        *,
        methods: tuple[str, ...] | list[str] = ("GET",),
        name: str | None = None,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self.add(pattern, fn, methods=methods, name=name)
            return fn

        return decorator

    def get(self, pattern: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(pattern, methods=("GET",), name=name)

    def post(self, pattern: str, *, name: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        return self.route(pattern, methods=("POST",), name=name)

    def include(self, prefix: str, other: Router, namespace: str | None = None) -> None:
        clean_prefix = prefix.rstrip("/")
        for r in other.routes:
            joined = f"{clean_prefix}/{r.pattern.lstrip('/')}" if clean_prefix else r.pattern
            rname = f"{namespace}:{r.name}" if (namespace and r.name) else r.name
            self.add(joined, r.handler, methods=r.methods, name=rname)

    def resolve(self, path: str, method: str) -> tuple[Route, dict[str, Any]] | None:
        method_up = method.upper()
        allowed: list[str] = []
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                if method_up in route.methods or (method_up == "HEAD" and "GET" in route.methods):
                    return route, params
                allowed.extend(route.methods)
        if allowed:
            raise HttpError(405, f"Method {method_up} not allowed. Allowed: {', '.join(sorted(set(allowed)))}")
        return None

    def url_for(self, name: str, **params: Any) -> str:
        if name not in self._named:
            raise KeyError(f"Unknown route name '{name}'")
        return self._named[name].build_url(**params)


def path(
    pattern: str,
    handler: Callable[..., Any],
    *,
    methods: tuple[str, ...] | list[str] = ("GET", "POST"),
    name: str | None = None,
) -> tuple[str, Callable[..., Any], tuple[str, ...], str | None]:
    """Declarative MTV-style route specification helper."""
    return (pattern, handler, tuple(m.upper() for m in methods), name)
