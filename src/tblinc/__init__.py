"""Top-level ``tblinc`` package aliasing ``tblinc_open_source`` and its submodules cleanly."""

from __future__ import annotations

import sys

import tblinc_open_source as _root
from tblinc_open_source import *  # noqa: F401, F403
from tblinc_open_source import __version__, ai_models, cli, generator, web

for _mod_name, _mod in list(sys.modules.items()):
    if _mod_name.startswith("tblinc_open_source."):
        _alias = "tblinc." + _mod_name[len("tblinc_open_source.") :]
        sys.modules.setdefault(_alias, _mod)

__path__ = list(_root.__path__)

__all__ = [
    "__version__",
    "ai_models",
    "cli",
    "generator",
    "web",
]
