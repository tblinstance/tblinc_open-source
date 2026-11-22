"""Custom pure-Python Template Engine with inheritance, blocks, includes, filters, and auto-escaping."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"(\{\{.*?\}\}|\{%.*?%\}|\{#.*?#\})", re.DOTALL)
_EXTENDS_RE = re.compile(r"^\s*\{%\s*extends\s+['\"]([^'\"]+)['\"]\s*%\}", re.DOTALL)
_BLOCK_TAG_RE = re.compile(
    r"\{%\s*(?:block\s+([a-zA-Z_][a-zA-Z0-9_]*)|endblock(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)\s*%\}"
)


def _extract_top_level_blocks(source: str) -> list[tuple[str, int, int, int, int]]:
    """Return (name, full_start, inner_start, inner_end, full_end) for top-level blocks."""
    blocks: list[tuple[str, int, int, int, int]] = []
    stack: list[tuple[str, int, int]] = []
    for match in _BLOCK_TAG_RE.finditer(source):
        bname = match.group(1)
        if bname is not None:
            stack.append((bname, match.start(), match.end()))
        elif stack:
            name, fstart, istart = stack.pop()
            if not stack:
                blocks.append((name, fstart, istart, match.start(), match.end()))
    return blocks


def _apply_block_overrides(source: str, overrides: dict[str, str]) -> str:
    """Recursively substitute matching blocks while preserving block wrappers for deeper inheritance."""
    top_blocks = _extract_top_level_blocks(source)
    if not top_blocks:
        return source
    out: list[str] = []
    cursor = 0
    for name, fstart, istart, iend, fend in top_blocks:
        out.append(source[cursor:fstart])
        inner = source[istart:iend]
        if name in overrides:
            replaced = overrides[name].replace("{{ block.super }}", inner)
            out.append(f"{{% block {name} %}}{replaced}{{% endblock %}}")
        else:
            nested = _apply_block_overrides(inner, overrides)
            out.append(f"{{% block {name} %}}{nested}{{% endblock %}}")
        cursor = fend
    out.append(source[cursor:])
    return "".join(out)


class SafeString(str):
    """Marks HTML content as trusted so auto-escaping does not double-escape it."""


def mark_safe(text: str) -> SafeString:
    return SafeString(text)


def _lookup(expr: str, ctx: dict[str, Any]) -> Any:
    expr = expr.strip()
    if not expr:
        return ""
    if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
        return expr[1:-1]
    if expr == "True" or expr == "true":
        return True
    if expr == "False" or expr == "false":
        return False
    if expr == "None" or expr == "none":
        return None
    if re.fullmatch(r"-?\d+", expr):
        return int(expr)
    if re.fullmatch(r"-?\d+\.\d+", expr):
        return float(expr)

    parts = expr.split(".")
    cur: Any = ctx.get(parts[0])
    for part in parts[1:]:
        if cur is None:
            return ""
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, (list, tuple)) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if 0 <= idx < len(cur) else ""
        else:
            cur = getattr(cur, part, "")
        if callable(cur):
            try:
                cur = cur()
            except TypeError:
                pass
    return cur


def _apply_filter(val: Any, flt: str) -> Any:
    name, arg = (flt.split(":", 1) + [None])[:2]
    name = name.strip()
    if arg is not None:
        arg = arg.strip().strip('"').strip("'")

    if name == "safe":
        return SafeString("" if val is None else str(val))
    if name == "upper":
        return str(val).upper()
    if name == "lower":
        return str(val).lower()
    if name == "title":
        return str(val).title()
    if name == "length":
        return len(val) if val is not None else 0
    if name == "json":
        return SafeString(json.dumps(val, indent=2, default=str))
    if name == "default":
        return arg if (val is None or val == "") else val
    if name == "truncate":
        limit = int(arg or 60)
        s = str(val)
        return (s[:limit] + "...") if len(s) > limit else s
    if name == "join":
        sep = arg if arg is not None else ", "
        return sep.join(str(x) for x in (val or []))
    return val


def _eval_expr(raw: str, ctx: dict[str, Any]) -> Any:
    # Split pipe filters outside quoted strings
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in raw:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in {"'", '"'}:
            quote = ch
            buf.append(ch)
        elif ch == "|":
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).strip())

    val = _lookup(parts[0], ctx)
    for flt in parts[1:]:
        if flt:
            val = _apply_filter(val, flt)
    return val


def _eval_condition(cond: str, ctx: dict[str, Any]) -> bool:
    cond = cond.strip()
    # Handle `or` then `and`
    if " or " in cond:
        return any(_eval_condition(part, ctx) for part in cond.split(" or "))
    if " and " in cond:
        return all(_eval_condition(part, ctx) for part in cond.split(" and "))
    if cond.startswith("not "):
        return not _eval_condition(cond[4:], ctx)

    for op in ("==", "!=", ">=", "<=", ">", "<", " not in ", " in "):
        if op in cond:
            left_s, right_s = cond.split(op, 1)
            left = _eval_expr(left_s, ctx)
            right = _eval_expr(right_s, ctx)
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == ">=":
                return left >= right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            if op == "<":
                return left < right
            if op == " in ":
                return left in (right or ())
            if op == " not in ":
                return left not in (right or ())

    return bool(_eval_expr(cond, ctx))


class TemplateEngine:
    """MTV template loader & renderer supporting extends/block/include/if/for/csrf_token."""

    def __init__(self, directories: list[str | Path] | None = None) -> None:
        self.directories: list[Path] = [Path(d) for d in (directories or [])]
        self.memory_templates: dict[str, str] = {}

    def add_directory(self, directory: str | Path) -> None:
        p = Path(directory)
        if p not in self.directories:
            self.directories.append(p)

    def register_template(self, name: str, source: str) -> None:
        self.memory_templates[name] = source

    def load_source(self, name: str) -> str:
        for d in self.directories:
            candidate = d / name
            if candidate.is_file():
                return candidate.read_text(encoding="utf-8")
        if name in self.memory_templates:
            return self.memory_templates[name]
        raise FileNotFoundError(f"Template '{name}' not found in {self.directories} or built-in templates.")

    def _resolve_inheritance(self, source: str) -> str:
        match = _EXTENDS_RE.match(source)
        if not match:
            return source
        parent_name = match.group(1)
        parent_src = self._resolve_inheritance(self.load_source(parent_name))
        child_blocks = {
            name: source[istart:iend]
            for name, _, istart, iend, _ in _extract_top_level_blocks(source)
        }
        return _apply_block_overrides(parent_src, child_blocks)

    def render(self, template_name: str, context: dict[str, Any] | None = None) -> str:
        src = self.load_source(template_name)
        return self.render_string(src, context)

    def render_string(self, source: str, context: dict[str, Any] | None = None) -> str:
        resolved = self._resolve_inheritance(source)
        # Strip any remaining standalone block markers
        resolved = re.sub(r"\{%\s*(?:block\s+[a-zA-Z_][a-zA-Z0-9_]*|endblock(?:\s+[a-zA-Z_][a-zA-Z0-9_]*)?)\s*%\}", "", resolved)
        tokens = _TOKEN_RE.split(resolved)
        nodes, _ = self._parse(tokens, 0)
        return self._eval_nodes(nodes, dict(context or {}))

    def _parse(self, tokens: list[str], pos: int, stop_tags: set[str] | None = None) -> tuple[list[tuple[Any, ...]], int]:
        nodes: list[tuple[Any, ...]] = []
        n = len(tokens)
        while pos < n:
            tok = tokens[pos]
            pos += 1
            if not tok:
                continue
            if tok.startswith("{#"):
                continue
            if tok.startswith("{{"):
                nodes.append(("var", tok[2:-2].strip()))
                continue
            if tok.startswith("{%"):
                tag = tok[2:-2].strip()
                head = tag.split(None, 1)[0] if tag else ""
                if stop_tags and head in stop_tags:
                    return nodes, pos - 1
                if head == "csrf_token":
                    nodes.append(("csrf",))
                elif head == "include":
                    inc_name = tag[7:].strip().strip('"').strip("'")
                    nodes.append(("include", inc_name))
                elif head == "if":
                    branches: list[tuple[str | None, list[tuple[Any, ...]]]] = []
                    cond = tag[2:].strip()
                    body, pos = self._parse(tokens, pos, {"elif", "else", "endif"})
                    branches.append((cond, body))
                    while pos < n:
                        next_tag = tokens[pos][2:-2].strip()
                        pos += 1
                        if next_tag.startswith("elif "):
                            econd = next_tag[5:].strip()
                            ebody, pos = self._parse(tokens, pos, {"elif", "else", "endif"})
                            branches.append((econd, ebody))
                        elif next_tag == "else":
                            ebody, pos = self._parse(tokens, pos, {"endif"})
                            branches.append((None, ebody))
                        elif next_tag == "endif":
                            break
                    nodes.append(("if", branches))
                elif head == "for":
                    m = re.match(r"for\s+([a-zA-Z_][a-zA-Z0-9_,\s]*)\s+in\s+(.+)", tag)
                    if not m:
                        raise SyntaxError(f"Invalid for tag: {tag}")
                    var_names = [v.strip() for v in m.group(1).split(",")]
                    iter_expr = m.group(2).strip()
                    loop_body, pos = self._parse(tokens, pos, {"empty", "endfor"})
                    empty_body: list[tuple[Any, ...]] = []
                    if pos < n:
                        end_tag = tokens[pos][2:-2].strip()
                        pos += 1
                        if end_tag == "empty":
                            empty_body, pos = self._parse(tokens, pos, {"endfor"})
                            if pos < n:
                                pos += 1  # consume endfor
                    nodes.append(("for", var_names, iter_expr, loop_body, empty_body))
                continue
            nodes.append(("text", tok))
        return nodes, pos

    def _eval_nodes(self, nodes: list[tuple[Any, ...]], ctx: dict[str, Any]) -> str:
        out: list[str] = []
        for node in nodes:
            kind = node[0]
            if kind == "text":
                out.append(node[1])
            elif kind == "var":
                val = _eval_expr(node[1], ctx)
                if val is None:
                    continue
                if isinstance(val, SafeString):
                    out.append(str(val))
                else:
                    out.append(html.escape(str(val), quote=True))
            elif kind == "csrf":
                tok = html.escape(str(ctx.get("csrf_token", "")), quote=True)
                out.append(f'<input type="hidden" name="csrf_token" value="{tok}">')
            elif kind == "include":
                out.append(self.render(node[1], ctx))
            elif kind == "if":
                for cond, branch in node[1]:
                    if cond is None or _eval_condition(cond, ctx):
                        out.append(self._eval_nodes(branch, ctx))
                        break
            elif kind == "for":
                var_names, iter_expr, loop_body, empty_body = node[1], node[2], node[3], node[4]
                seq = _eval_expr(iter_expr, ctx)
                items = list(seq) if seq is not None else []
                if not items:
                    out.append(self._eval_nodes(empty_body, ctx))
                    continue
                total = len(items)
                for idx, item in enumerate(items):
                    local = dict(ctx)
                    if len(var_names) == 1:
                        local[var_names[0]] = item
                    else:
                        for vn, sub in zip(var_names, item):
                            local[vn] = sub
                    local["loop"] = {
                        "index": idx + 1,
                        "index0": idx,
                        "first": idx == 0,
                        "last": idx == total - 1,
                        "length": total,
                    }
                    out.append(self._eval_nodes(loop_body, local))
        return "".join(out)
