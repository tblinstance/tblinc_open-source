"""Static CSS & JS theme/responsive assets for generated tblinc AI web applications."""

from __future__ import annotations


def build_theme_assets() -> dict[str, str]:
    """Return static Light/Dark CSS and interactive JS controller files."""
    return {
        "static/css/theme.css": """/* 100% Light & Dark + PC / Tablet / Mobile responsive styles */
:root {
  --surface-glass: rgba(255, 255, 255, 0.86);
  --surface-border: rgba(226, 232, 240, 0.9);
  --hero-glow: radial-gradient(circle at top right, rgba(99, 102, 241, 0.16), transparent 55%);
}

html.dark {
  --surface-glass: rgba(15, 23, 42, 0.78);
  --surface-border: rgba(30, 41, 59, 0.9);
  --hero-glow: radial-gradient(circle at top right, rgba(56, 189, 248, 0.18), transparent 55%);
}

html {
  font-size: 14px;
  height: 100%;
}

html, body {
  font-family: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 0.875rem;
  line-height: 1.45;
  -webkit-tap-highlight-color: transparent;
}

code, pre, .font-mono {
  font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace;
}

button, a {
  touch-action: manipulation;
}

.glass-panel {
  background: var(--surface-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.hero-backdrop {
  background-image: var(--hero-glow);
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}

.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

@media (min-width: 1024px) {
  .tblinc-sidenav {
    width: 16rem;
    transition: width 0.2s ease;
  }
  .tblinc-sidenav[data-sidenav-mode="mini"] {
    width: 4.5rem;
  }
  .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-label] {
    display: none !important;
  }
  .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-item] {
    justify-content: center;
    padding-left: 0;
    padding-right: 0;
  }
  .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-brand] {
    justify-content: center;
    padding-left: 0.75rem;
    padding-right: 0.75rem;
  }
  .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-footer] {
    justify-content: center;
    flex-direction: column;
    gap: 0.5rem;
  }
  .tblinc-sidenav[data-sidenav-mode="hidden"] {
    display: none !important;
  }
}
""",
        "static/js/app.js": """/* Unified Light/Dark theme, collapsible Sidenav (Expanded/Icon-Only/Hidden), mobile drawer, AI runner & toast */
(function () {
  const STORAGE_KEY = "tblinc-theme";
  const SIDENAV_KEY = "tblinc-site-sidenav";
  const SIDENAV_PREV_KEY = "tblinc-site-sidenav-prev";

  function applySiteSidenav(mode) {
    const nav = document.getElementById("site-desktop-sidenav");
    if (!nav) return;
    const valid = mode === "mini" ? "mini" : "expanded";
    nav.setAttribute("data-sidenav-mode", valid);
    localStorage.setItem(SIDENAV_KEY, valid);
    nav.style.removeProperty("display");
    nav.style.width = valid === "mini" ? "4.5rem" : "16rem";
    nav.querySelectorAll("[data-sidenav-label]").forEach((el) => {
      el.style.display = valid === "mini" ? "none" : "";
    });
    nav.querySelectorAll("[data-sidenav-item], [data-sidenav-brand]").forEach((el) => {
      el.style.justifyContent = valid === "mini" ? "center" : "";
    });
    document.querySelectorAll("[data-site-nav-icon-collapse]").forEach((el) => el.classList.toggle("hidden", valid === "mini"));
    document.querySelectorAll("[data-site-nav-icon-expand]").forEach((el) => el.classList.toggle("hidden", valid !== "mini"));
  }
  window.tblincApplySiteSidenav = applySiteSidenav;
  window.tblincToggleSidenav = function () {
    if (window.innerWidth >= 1024) {
      window.tblincToggleSiteSidenavMini();
    } else {
      window.tblincToggleMobileMenu();
    }
  };

  window.tblincToggleSiteSidenavHidden = function () {
    const nav = document.getElementById("site-desktop-sidenav");
    if (!nav) return;
    const cur = nav.getAttribute("data-sidenav-mode") || "expanded";
    if (cur === "hidden") {
      const prev = localStorage.getItem(SIDENAV_PREV_KEY) || "expanded";
      applySiteSidenav(prev === "hidden" ? "expanded" : prev);
    } else {
      localStorage.setItem(SIDENAV_PREV_KEY, cur);
      applySiteSidenav("hidden");
    }
  };

  window.tblincToggleSiteSidenavMini = function () {
    const nav = document.getElementById("site-desktop-sidenav");
    if (!nav) return;
    const cur = nav.getAttribute("data-sidenav-mode") || "expanded";
    applySiteSidenav(cur === "mini" ? "expanded" : "mini");
  };

  function applyTheme(mode) {
    const isDark = mode === "dark";
    document.documentElement.classList.toggle("dark", isDark);
    document.documentElement.dataset.theme = isDark ? "dark" : "light";
    document.querySelectorAll("[data-theme-label]").forEach((el) => {
      el.textContent = isDark ? "Light" : "Dark";
    });
    document.querySelectorAll("[data-theme-sun]").forEach((el) => {
      el.classList.toggle("hidden", !isDark);
    });
    document.querySelectorAll("[data-theme-moon]").forEach((el) => {
      el.classList.toggle("hidden", isDark);
    });
  }

  window.tblincToast = function (message) {
    let el = document.getElementById("tblinc-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "tblinc-toast";
      el.className = "fixed bottom-20 md:bottom-6 right-4 sm:right-6 z-50 px-4 py-2.5 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-semibold shadow-xl transition";
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.remove("hidden");
    if (window.Motion && window.Motion.animate) {
      window.Motion.animate(el, { opacity: [0, 1], y: [10, 0] }, { duration: 0.22 });
    }
    clearTimeout(window.__tblincToastTimer);
    window.__tblincToastTimer = setTimeout(() => el.classList.add("hidden"), 2200);
  };

  window.tblincToggleTheme = function () {
    const nextMode = document.documentElement.classList.contains("dark") ? "light" : "dark";
    localStorage.setItem(STORAGE_KEY, nextMode);
    applyTheme(nextMode);
    if (window.Motion && window.Motion.animate) {
      document.querySelectorAll("[data-theme-btn]").forEach((btn) => {
        window.Motion.animate(btn, { scale: [0.92, 1.08, 1] }, { duration: 0.28 });
      });
    }
    window.tblincToast("Switched to " + (nextMode === "dark" ? "Dark" : "Light") + " theme");
  };

  window.tblincToggleMobileMenu = function (forceOpen) {
    const drawer = document.getElementById("mobile-nav-drawer");
    const backdrop = document.getElementById("mobile-nav-backdrop");
    if (!drawer || !backdrop) return;
    const shouldOpen = typeof forceOpen === "boolean" ? forceOpen : drawer.classList.contains("hidden");
    drawer.classList.toggle("hidden", !shouldOpen);
    backdrop.classList.toggle("hidden", !shouldOpen);
    document.body.classList.toggle("overflow-hidden", shouldOpen);
    if (shouldOpen && window.Motion && window.Motion.animate) {
      window.Motion.animate(drawer, { x: [280, 0], opacity: [0.6, 1] }, { duration: 0.24 });
    }
  };

  window.tblincRunModel = async function (key, prefix) {
    const inp = document.getElementById(prefix + "-inp-" + key);
    const outWrap = document.getElementById(prefix + "-wrap-" + key);
    const out = document.getElementById(prefix + "-out-" + key);
    const badge = document.getElementById(prefix + "-lat-" + key);
    if (outWrap) outWrap.classList.remove("hidden");
    out.textContent = "Running " + key + "...";
    try {
      const body = inp && inp.value.trim() ? JSON.parse(inp.value) : null;
      const headers = { "Content-Type": "application/json" };
      const savedKey = (localStorage.getItem("tblinc-user-api-key") || "").trim();
      if (savedKey) headers["X-API-Key"] = savedKey;
      const res = await fetch("/api/predict/" + encodeURIComponent(key) + "/", {
        method: "POST",
        headers,
        body: JSON.stringify({ input: body })
      });
      const data = await res.json();
      const payload = data.result || data;
      out.textContent = JSON.stringify(payload, null, 2);
      if (badge && payload.latency_ms !== undefined) {
        badge.textContent = payload.latency_ms + " ms";
      }
      if (window.Motion && window.Motion.animate && outWrap) {
        window.Motion.animate(outWrap, { opacity: [0, 1], y: [6, 0] }, { duration: 0.24 });
      }
    } catch (err) {
      out.textContent = "Error: " + err.message;
    }
  };

  window.tblincCopyOutput = function (elId) {
    const el = document.getElementById(elId);
    if (!el || !navigator.clipboard) return;
    navigator.clipboard.writeText(el.textContent || "").then(() => window.tblincToast("Copied output JSON"));
  };

  window.tblincFilterModels = function (query) {
    const q = (query || "").trim().toLowerCase();
    document.querySelectorAll("[data-model-card]").forEach((card) => {
      const hay = (card.dataset.search || "").toLowerCase();
      card.classList.toggle("hidden", Boolean(q) && !hay.includes(q));
    });
  };

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      window.tblincToggleMobileMenu(false);
    }
  });

  window.addEventListener("DOMContentLoaded", () => {
    const saved = localStorage.getItem(STORAGE_KEY);
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(saved || (prefersDark ? "dark" : "light"));
    applySiteSidenav(localStorage.getItem(SIDENAV_KEY) || "expanded");

    if (window.lucide) {
      window.lucide.createIcons();
    }
    if (window.Motion && window.Motion.animate) {
      const { animate, stagger } = window.Motion;
      const hero = document.querySelector("[data-motion='hero']");
      if (hero) {
        animate(hero, { opacity: [0, 1], y: [14, 0] }, { duration: 0.48 });
      }
      const cards = document.querySelectorAll("[data-motion='card']");
      if (cards.length) {
        animate(cards, { opacity: [0, 1], y: [16, 0] }, { duration: 0.42, delay: stagger ? stagger(0.04) : 0 });
      }
    }
  });
})();
""",
    }
