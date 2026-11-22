"""Built-in Tailwind CSS + Lucide Icons + Motion CDN templates: 100% Light/Dark & PC/Tablet/Mobile responsive."""

from __future__ import annotations

from .engine import TemplateEngine

BASE_LAYOUT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <title>{% block title %}{{ site_title|default:"tblinc AI" }}{% endblock %}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: "class",
      theme: {
        extend: {
          fontFamily: {
            sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
            mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
          },
        },
      },
    };
    (function () {
      const saved = localStorage.getItem("tblinc-theme");
      const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      const isDark = saved ? saved === "dark" : prefersDark;
      document.documentElement.classList.toggle("dark", isDark);
    })();
  </script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/motion@latest/dist/motion.js"></script>
  <style>
    html { font-size: 14px; }
    body { font-family: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 0.875rem; line-height: 1.45; -webkit-tap-highlight-color: transparent; }
    code, pre, .font-mono { font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace; }
    .glass { background: rgba(255, 255, 255, 0.84); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }
    .dark .glass { background: rgba(15, 23, 42, 0.78); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }
    .no-scrollbar::-webkit-scrollbar { display: none; }
    .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
    @media (min-width: 1024px) {
      .tblinc-sidenav { width: 16rem; transition: width 0.2s ease; }
      .tblinc-sidenav[data-sidenav-mode="mini"] { width: 4.5rem; }
      .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-label] { display: none !important; }
      .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-item] { justify-content: center; padding-left: 0; padding-right: 0; }
      .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-brand] { justify-content: center; padding-left: 0.75rem; padding-right: 0.75rem; }
      .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-footer] { justify-content: center; flex-direction: column; gap: 0.5rem; }
      .tblinc-sidenav[data-sidenav-mode="hidden"] { display: none !important; }
    }
  </style>
  {% block head %}{% endblock %}
</head>
<body class="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 antialiased transition-colors duration-200 selection:bg-indigo-500/25 selection:text-indigo-900 dark:selection:text-indigo-200 overflow-x-hidden">
  {% block body %}{% endblock %}
  <script>
    function tblincSyncThemeUI() {
      const isDark = document.documentElement.classList.contains("dark");
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
    function tblincToggleTheme() {
      const isDark = document.documentElement.classList.toggle("dark");
      localStorage.setItem("tblinc-theme", isDark ? "dark" : "light");
      tblincSyncThemeUI();
      if (window.Motion && window.Motion.animate) {
        document.querySelectorAll("[data-theme-btn]").forEach((btn) => {
          window.Motion.animate(btn, { scale: [0.92, 1.06, 1] }, { duration: 0.28 });
        });
      }
    }
    function tblincApplyAdminSidenav(mode) {
      const nav = document.getElementById("admin-desktop-sidenav");
      if (!nav) return;
      const valid = mode === "mini" ? "mini" : "expanded";
      nav.setAttribute("data-sidenav-mode", valid);
      localStorage.setItem("tblinc-admin-sidenav", valid);
      nav.style.removeProperty("display");
      nav.style.width = valid === "mini" ? "4.5rem" : "16rem";
      nav.querySelectorAll("[data-sidenav-label]").forEach((el) => {
        el.style.display = valid === "mini" ? "none" : "";
      });
      nav.querySelectorAll("[data-sidenav-item], [data-sidenav-brand]").forEach((el) => {
        el.style.justifyContent = valid === "mini" ? "center" : "";
      });
      document.querySelectorAll("[data-admin-nav-icon-collapse]").forEach((el) => el.classList.toggle("hidden", valid === "mini"));
      document.querySelectorAll("[data-admin-nav-icon-expand]").forEach((el) => el.classList.toggle("hidden", valid !== "mini"));
    }
    function tblincToggleAdminSidenavHidden() {
      const nav = document.getElementById("admin-desktop-sidenav");
      if (!nav) return;
      const cur = nav.getAttribute("data-sidenav-mode") || "expanded";
      if (cur === "hidden") {
        const prev = localStorage.getItem("tblinc-admin-sidenav-prev") || "expanded";
        tblincApplyAdminSidenav(prev === "hidden" ? "expanded" : prev);
      } else {
        localStorage.setItem("tblinc-admin-sidenav-prev", cur);
        tblincApplyAdminSidenav("hidden");
      }
    }
    function tblincToggleAdminSidenavMini() {
      const nav = document.getElementById("admin-desktop-sidenav");
      if (!nav) return;
      const cur = nav.getAttribute("data-sidenav-mode") || "expanded";
      tblincApplyAdminSidenav(cur === "mini" ? "expanded" : "mini");
    }
    function tblincToggleAdminDrawer(forceOpen) {
      const drawer = document.getElementById("admin-mobile-drawer");
      const backdrop = document.getElementById("admin-mobile-backdrop");
      if (!drawer || !backdrop) return;
      const shouldOpen = typeof forceOpen === "boolean" ? forceOpen : drawer.classList.contains("hidden");
      drawer.classList.toggle("hidden", !shouldOpen);
      backdrop.classList.toggle("hidden", !shouldOpen);
      document.body.classList.toggle("overflow-hidden", shouldOpen);
      if (shouldOpen && window.Motion && window.Motion.animate) {
        window.Motion.animate(drawer, { x: [-280, 0], opacity: [0.6, 1] }, { duration: 0.24 });
      }
    }
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { tblincToggleAdminDrawer(false); }
    });
    if (window.lucide) { window.lucide.createIcons(); }
    tblincSyncThemeUI();
    tblincApplyAdminSidenav(localStorage.getItem("tblinc-admin-sidenav") || "expanded");
    if (window.Motion && window.Motion.animate) {
      const { animate, stagger } = window.Motion;
      const cards = document.querySelectorAll("[data-motion='card']");
      if (cards.length) {
        animate(cards, { opacity: [0, 1], y: [14, 0] }, { duration: 0.42, delay: stagger ? stagger(0.04) : 0 });
      }
      const hero = document.querySelector("[data-motion='hero']");
      if (hero) {
        animate(hero, { opacity: [0, 1], y: [10, 0] }, { duration: 0.48 });
      }
    }
  </script>
  {% block scripts %}{% endblock %}
</body>
</html>
"""

AUTH_TEMPLATE = """{% extends "tblinc_base.html" %}
{% block title %}{{ title }} · {{ site_title|default:"tblinc AI" }}{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center p-4 sm:p-6 lg:p-8 bg-gradient-to-br from-slate-100 via-indigo-50/70 to-cyan-50/60 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/50 transition-colors">
  <button type="button" data-theme-btn onclick="tblincToggleTheme()" aria-label="Toggle Light/Dark theme" class="fixed top-4 right-4 sm:top-5 sm:right-5 inline-flex items-center gap-1.5 px-3 py-2 min-h-[40px] rounded-xl glass border border-slate-200 dark:border-slate-800 text-xs font-medium text-slate-700 dark:text-slate-200 shadow-sm hover:border-indigo-400 transition">
    <i data-lucide="sun" data-theme-sun class="w-4 h-4 text-amber-500 hidden"></i>
    <i data-lucide="moon" data-theme-moon class="w-4 h-4 text-indigo-600"></i>
    <span data-theme-label>Dark</span>
  </button>
  <div data-motion="hero" class="w-full max-w-md glass border border-slate-200 dark:border-slate-800 rounded-2xl sm:rounded-3xl p-6 sm:p-8 shadow-2xl shadow-slate-900/10 dark:shadow-indigo-950/40">
    <div class="flex items-center gap-3 mb-5">
      <div class="h-11 w-11 rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30 shrink-0">
        <i data-lucide="cpu" class="w-6 h-6 text-white"></i>
      </div>
      <div class="min-w-0">
        <h1 class="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-white truncate">{{ title }}</h1>
        <p class="text-xs text-slate-500 dark:text-slate-400">{{ subtitle }}</p>
      </div>
    </div>
    {% if alt_url %}
    <div class="grid grid-cols-2 gap-1.5 p-1 rounded-xl bg-slate-100 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 mb-5 text-xs font-semibold">
      <a href="{{ login_url|default:'/auth/login/' }}" class="py-2 rounded-lg text-center transition {% if auth_mode == 'login' %}bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm{% else %}text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white{% endif %}">Sign In</a>
      <a href="{{ register_url|default:'/auth/register/' }}" class="py-2 rounded-lg text-center transition {% if auth_mode == 'register' %}bg-white dark:bg-slate-800 text-indigo-600 dark:text-indigo-400 shadow-sm{% else %}text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white{% endif %}">Sign Up</a>
    </div>
    {% endif %}
    <form method="post" class="space-y-4">
      {% csrf_token %}
      <input type="hidden" name="next" value="{{ next_url|default:'/' }}">
      {{ form_html|safe }}
      <button type="submit" class="w-full mt-2 min-h-[44px] inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-2.5 px-4 shadow-lg shadow-indigo-600/25 transition">
        <i data-lucide="log-in" class="w-4 h-4"></i>
        <span>{{ button_label|default:"Continue" }}</span>
      </button>
    </form>
    {% if alt_url %}
    <p class="mt-6 text-center text-xs text-slate-500 dark:text-slate-400">
      {{ alt_text }} <a href="{{ alt_url }}" class="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">{{ alt_label }}</a>
    </p>
    {% endif %}
    <div class="mt-5 pt-4 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
      <a href="/" class="inline-flex items-center gap-1 hover:text-slate-900 dark:hover:text-slate-200"><i data-lucide="arrow-left" class="w-3.5 h-3.5"></i> Home</a>
      <span>tblinc AI</span>
    </div>
  </div>
</div>
{% endblock %}
"""

ADMIN_LAYOUT = """{% extends "tblinc_base.html" %}
{% block body %}
<div class="h-screen flex bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 transition-colors overflow-hidden">
  <!-- Mobile/Tablet Slide-Over Backdrop -->
  <div id="admin-mobile-backdrop" onclick="tblincToggleAdminDrawer(false)" class="hidden fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"></div>

  <!-- Mobile & Tablet Slide-Over Sidebar Drawer (< lg) -->
  <aside id="admin-mobile-drawer" class="hidden fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] flex flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl lg:hidden">
    <div class="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
      <div class="flex items-center gap-2.5">
        <div class="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-600 to-cyan-500 flex items-center justify-center shadow">
          <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
        </div>
        <div class="font-bold text-sm text-slate-900 dark:text-white tracking-tight">tblinc AI</div>
      </div>
      <button type="button" onclick="tblincToggleAdminDrawer(false)" aria-label="Close navigation menu" class="p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="x" class="w-5 h-5"></i>
      </button>
    </div>
    <nav class="flex-1 p-4 space-y-1.5 overflow-y-auto">
      <div class="pb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Workspace</div>
      <a href="{{ admin_prefix }}/" class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="layout-dashboard" class="w-4 h-4 text-indigo-600 dark:text-indigo-400"></i>
        <span>Dashboard</span>
      </a>
      <a href="{{ admin_prefix }}/ai/" class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="message-square-text" class="w-4 h-4 text-cyan-600 dark:text-cyan-400"></i>
        <span>ai_chat</span>
      </a>
      <a href="{{ admin_prefix }}/models/" class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="brain-circuit" class="w-4 h-4 text-violet-600 dark:text-violet-400"></i>
        <span>Models</span>
        <span class="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-700 dark:text-violet-300 border border-violet-500/30">{{ ai_model_count }}</span>
      </a>
      <a href="{{ admin_prefix }}/train/" class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="flame" class="w-4 h-4 text-amber-500"></i>
        <span>Training</span>
      </a>
      <a href="{{ admin_prefix }}/keys/" class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i>
        <span>Keys &amp; Quotas</span>
      </a>
      <a href="{{ admin_prefix }}/settings/" class="flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="settings" class="w-4 h-4 text-slate-500 dark:text-slate-400"></i>
        <span>Settings</span>
      </a>
      <div class="pt-4 pb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Database</div>
      {% for m in registered_models %}
      <a href="{{ admin_prefix }}/{{ m.slug }}/" class="flex items-center justify-between px-3 py-2.5 rounded-xl text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800">
        <span class="flex items-center gap-2.5"><i data-lucide="{{ m.icon|default:'table-2' }}" class="w-4 h-4 text-slate-400"></i><span>{{ m.label|default:m.verbose_plural }}</span></span>
        <span class="text-xs px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">{{ m.count }}</span>
      </a>
      {% endfor %}
    </nav>
    <div class="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
      <span class="text-slate-500 dark:text-slate-400 truncate">{{ current_user.username|default:"admin" }}</span>
      <a href="{{ admin_prefix }}/logout/" class="text-rose-600 dark:text-rose-400 font-medium inline-flex items-center gap-1"><i data-lucide="log-out" class="w-3.5 h-3.5"></i> Sign Out</a>
    </div>
  </aside>

  <!-- Desktop (PC) Collapsible Persistent Sidebar (Expanded · Icon-Only) -->
  <aside id="admin-desktop-sidenav" data-sidenav-mode="expanded" class="tblinc-sidenav hidden lg:flex flex-col shrink-0 border-r border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-900/60 backdrop-blur-xl h-full">
    <div data-sidenav-brand class="h-16 px-4 border-b border-slate-200 dark:border-slate-800/80 flex items-center gap-3 shrink-0">
      <a href="{{ admin_prefix }}/" title="tblinc AI" class="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
        <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
      </a>
      <div data-sidenav-label class="min-w-0">
        <div class="font-bold text-sm text-slate-900 dark:text-white leading-tight tracking-tight truncate">tblinc AI</div>
      </div>
    </div>
    <nav class="flex-1 p-3 space-y-1 overflow-y-auto no-scrollbar">
      <div data-sidenav-label class="px-3 pt-1 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Workspace</div>
      <a href="{{ admin_prefix }}/" title="Dashboard" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="layout-dashboard" class="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0"></i>
        <span data-sidenav-label class="truncate">Dashboard</span>
      </a>
      <a href="{{ admin_prefix }}/ai/" title="ai_chat" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="message-square-text" class="w-4 h-4 text-cyan-600 dark:text-cyan-400 shrink-0"></i>
        <span data-sidenav-label class="truncate">ai_chat</span>
      </a>
      <a href="{{ admin_prefix }}/models/" title="Models ({{ ai_model_count }})" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="brain-circuit" class="w-4 h-4 text-violet-600 dark:text-violet-400 shrink-0"></i>
        <span data-sidenav-label class="truncate">Models</span>
        <span data-sidenav-label class="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-700 dark:text-violet-300 border border-violet-500/30 shrink-0">{{ ai_model_count }}</span>
      </a>
      <a href="{{ admin_prefix }}/train/" title="Training" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="flame" class="w-4 h-4 text-amber-500 shrink-0"></i>
        <span data-sidenav-label class="truncate">Training</span>
      </a>
      <a href="{{ admin_prefix }}/keys/" title="Keys & Quotas" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="key-round" class="w-4 h-4 text-emerald-500 shrink-0"></i>
        <span data-sidenav-label class="truncate">Keys &amp; Quotas</span>
      </a>
      <a href="{{ admin_prefix }}/settings/" title="Settings" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="settings" class="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0"></i>
        <span data-sidenav-label class="truncate">Settings</span>
      </a>
      <div data-sidenav-label class="pt-4 pb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Database</div>
      {% for m in registered_models %}
      <a href="{{ admin_prefix }}/{{ m.slug }}/" title="{{ m.label|default:m.verbose_plural }} ({{ m.count }})" data-sidenav-item class="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-slate-900 dark:hover:text-white transition">
        <i data-lucide="{{ m.icon|default:'table-2' }}" class="w-4 h-4 text-slate-400 shrink-0"></i>
        <span data-sidenav-label class="truncate flex-1">{{ m.label|default:m.verbose_plural }}</span>
        <span data-sidenav-label class="text-xs px-2 py-0.5 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 shrink-0">{{ m.count }}</span>
      </a>
      {% endfor %}
    </nav>
    <div data-sidenav-footer class="p-3 border-t border-slate-200 dark:border-slate-800/80 flex items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
      <span data-sidenav-label class="px-2 truncate">{{ current_user.username|default:"admin" }}</span>
      <a href="{{ admin_prefix }}/logout/" title="Sign Out ({{ current_user.username|default:'admin' }})" class="p-2 rounded-xl border border-rose-200 dark:border-rose-500/30 text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 inline-flex items-center justify-center shrink-0 transition">
        <i data-lucide="log-out" class="w-4 h-4"></i>
      </a>
    </div>
  </aside>

  <!-- Main area -->
  <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
    <header class="shrink-0 z-30 h-16 border-b border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-900/85 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between gap-3">
      <div class="flex items-center gap-2 min-w-0">
        <button type="button" data-admin-menu-btn onclick="tblincToggleAdminDrawer(true)" aria-label="Open admin menu" class="lg:hidden p-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800">
          <i data-lucide="chevrons-right" class="w-5 h-5"></i>
        </button>
        <button type="button" onclick="tblincToggleAdminSidenavMini()" title="Toggle Icon-Only Sidenav" aria-label="Toggle icon-only admin sidenav" class="hidden lg:inline-flex items-center justify-center p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:border-indigo-400 transition shrink-0">
          <i data-lucide="chevrons-left" data-admin-nav-icon-collapse class="w-4 h-4"></i>
          <i data-lucide="chevrons-right" data-admin-nav-icon-expand class="w-4 h-4 hidden"></i>
        </button>
        <h1 class="text-base sm:text-lg font-semibold text-slate-900 dark:text-white truncate ml-1">{% block header_title %}Dashboard{% endblock %}</h1>
      </div>
      <div class="flex items-center gap-2 text-xs shrink-0">
        <button type="button" data-theme-btn onclick="tblincToggleTheme()" aria-label="Toggle Light/Dark theme" class="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
          <i data-lucide="sun" data-theme-sun class="w-4 h-4 text-amber-500 hidden"></i>
          <i data-lucide="moon" data-theme-moon class="w-4 h-4 text-indigo-600"></i>
          <span data-theme-label class="hidden sm:inline">Dark</span>
        </button>
        <a href="/" class="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition">
          <i data-lucide="globe" class="w-3.5 h-3.5"></i> View Site
        </a>
        <a href="{{ admin_prefix }}/train/" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold transition shadow-sm">
          <i data-lucide="flame" class="w-3.5 h-3.5"></i> <span class="hidden sm:inline">Training</span>
        </a>
        <a href="{{ admin_prefix }}/ai/" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition shadow-sm">
          <i data-lucide="message-square-text" class="w-3.5 h-3.5"></i> <span class="hidden sm:inline">ai_chat</span>
        </a>
      </div>
    </header>
    <main class="flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-6 lg:p-8 pb-24 lg:pb-8 w-full space-y-6">
      {% block admin_content %}{% endblock %}
    </main>
  </div>

  <!-- Mobile Bottom Tab Bar (< md) -->
  <nav aria-label="Admin mobile navigation" class="md:hidden fixed bottom-0 inset-x-0 z-30 border-t border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-950/95 backdrop-blur-xl">
    <div class="grid grid-cols-5 text-[10px] font-medium">
      <a href="{{ admin_prefix }}/" class="flex flex-col items-center justify-center py-2.5 gap-1 text-slate-600 dark:text-slate-300 active:text-indigo-600">
        <i data-lucide="layout-dashboard" class="w-4 h-4"></i><span>Home</span>
      </a>
      <a href="{{ admin_prefix }}/train/" class="flex flex-col items-center justify-center py-2.5 gap-1 text-amber-600 dark:text-amber-400">
        <i data-lucide="flame" class="w-4 h-4"></i><span>Train</span>
      </a>
      <a href="{{ admin_prefix }}/ai/" class="flex flex-col items-center justify-center py-2.5 gap-1 text-slate-600 dark:text-slate-300 active:text-indigo-600">
        <i data-lucide="message-square-text" class="w-4 h-4"></i><span>ai_chat</span>
      </a>
      <button type="button" onclick="tblincToggleAdminDrawer(true)" class="flex flex-col items-center justify-center py-2.5 gap-1 text-slate-600 dark:text-slate-300 active:text-indigo-600">
        <i data-lucide="database" class="w-4 h-4"></i><span>Data</span>
      </button>
      <a href="/" class="flex flex-col items-center justify-center py-2.5 gap-1 text-slate-600 dark:text-slate-300 active:text-indigo-600">
        <i data-lucide="globe" class="w-4 h-4"></i><span>Site</span>
      </a>
    </div>
  </nav>
</div>
{% endblock %}
"""

ADMIN_DASHBOARD = """{% extends "tblinc_admin_base.html" %}
{% block title %}Dashboard · {{ admin_title }}{% endblock %}
{% block header_title %}Dashboard{% endblock %}
{% block admin_content %}
<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
  <a href="{{ admin_prefix }}/user/" data-motion="card" class="glass border border-slate-200 dark:border-slate-800 hover:border-indigo-400 rounded-2xl p-5 shadow-sm transition block">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Users &amp; Balances</span>
      <i data-lucide="users" class="w-4 h-4 text-indigo-600 dark:text-indigo-400"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ db_stats.user_count }}</div>
    <div class="mt-1 text-xs text-emerald-600 dark:text-emerald-400 font-mono">${{ db_stats.total_balance_usd }} total balance</div>
  </a>
  <a href="{{ admin_prefix }}/keys/" data-motion="card" class="glass border border-slate-200 dark:border-slate-800 hover:border-emerald-400 rounded-2xl p-5 shadow-sm transition block">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Active AI Keys</span>
      <i data-lucide="key-round" class="w-4 h-4 text-emerald-600 dark:text-emerald-400"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ db_stats.active_keys }} <span class="text-sm font-normal text-slate-400">/ {{ db_stats.total_keys }}</span></div>
    <div class="mt-1 text-xs text-slate-500">{{ db_stats.training_count }} trained model artifacts</div>
  </a>
  <a href="{{ admin_prefix }}/tokenusagelog/" data-motion="card" class="glass border border-slate-200 dark:border-slate-800 hover:border-cyan-400 rounded-2xl p-5 shadow-sm transition block">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Token Usage &amp; Calls</span>
      <i data-lucide="bar-chart-3" class="w-4 h-4 text-cyan-600 dark:text-cyan-400"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ db_stats.total_tokens }}</div>
    <div class="mt-1 text-xs text-slate-500 font-mono">{{ db_stats.total_requests }} logged AI requests</div>
  </a>
  <a href="{{ admin_prefix }}/billingtransaction/" data-motion="card" class="glass border border-slate-200 dark:border-slate-800 hover:border-amber-400 rounded-2xl p-5 shadow-sm transition block">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Billing &amp; SQLite DB</span>
      <i data-lucide="database" class="w-4 h-4 text-amber-500 dark:text-amber-400"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-emerald-600 dark:text-emerald-400">${{ db_stats.total_credited_usd }}</div>
    <div class="mt-1 text-xs text-slate-500 font-mono">${{ db_stats.total_spent_usd }} spent · {{ total_records }} rows ({{ db_stats.db_size_display }})</div>
  </a>
</div>

<section class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-1">
    <h2 class="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="database" class="w-4 h-4 text-indigo-600 dark:text-indigo-400"></i> SQLite Database Tables ({{ total_models }} tables · {{ total_records }} rows)
    </h2>
    <code class="text-[11px] font-mono text-slate-500 dark:text-slate-400 truncate">{{ db_stats.db_path }}</code>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[560px] text-left text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">Model</th>
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">SQLite Table</th>
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">Live Rows</th>
          <th class="px-4 sm:px-6 py-3.5 text-right font-semibold whitespace-nowrap">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/80">
        {% for m in registered_models %}
        <tr class="hover:bg-slate-100/70 dark:hover:bg-slate-800/30 transition">
          <td class="px-4 sm:px-6 py-3.5 font-semibold text-slate-900 dark:text-white">
            <a href="{{ admin_prefix }}/{{ m.slug }}/" class="inline-flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 transition">
              <i data-lucide="{{ m.icon|default:'table-2' }}" class="w-4 h-4 text-slate-400"></i>
              <span>{{ m.label|default:m.verbose_plural }}</span>
            </a>
          </td>
          <td class="px-4 sm:px-6 py-3.5 text-xs">
            <code class="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">{{ m.table }}</code>
          </td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs font-semibold text-slate-700 dark:text-slate-200">{{ m.count }}</td>
          <td class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap space-x-2">
            <a href="{{ admin_prefix }}/{{ m.slug }}/create/" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 dark:bg-indigo-600/20 hover:bg-indigo-100 dark:hover:bg-indigo-600/30 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 text-xs font-medium transition">
              <i data-lucide="plus" class="w-3.5 h-3.5"></i> Add
            </a>
            <a href="{{ admin_prefix }}/{{ m.slug }}/" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-medium transition">
              <i data-lucide="list" class="w-3.5 h-3.5"></i> Manage
            </a>
          </td>
        </tr>
        {% empty %}
        <tr>
          <td colspan="4" class="p-8 text-center text-sm text-slate-500 dark:text-slate-400">No models registered yet. Call <code>app.admin.register(YourModel)</code>.</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<!-- Live Database Records: Recent Users & Recent Billing Transactions -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
  <section class="glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
    <div class="px-4 sm:px-6 py-3.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
        <i data-lucide="users" class="w-4 h-4 text-indigo-500"></i> Recent Users (`tblinc_users`)
      </h3>
      <a href="{{ admin_prefix }}/user/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">View all &rarr;</a>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-100 dark:bg-slate-900/90 uppercase text-slate-500 border-b border-slate-200 dark:border-slate-800">
          <tr>
            <th class="px-4 py-2.5">Username</th>
            <th class="px-4 py-2.5">Role</th>
            <th class="px-4 py-2.5">Plan</th>
            <th class="px-4 py-2.5 text-right">Balance</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
          {% for u in recent_users %}
          <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/30">
            <td class="px-4 py-2.5 font-semibold text-slate-900 dark:text-white">
              <a href="{{ admin_prefix }}/user/{{ u.id }}/edit/" class="hover:text-indigo-500">{{ u.username }}</a>
            </td>
            <td class="px-4 py-2.5 text-slate-500">{% if u.is_staff %}Admin{% else %}User{% endif %}</td>
            <td class="px-4 py-2.5 font-mono uppercase text-indigo-600 dark:text-indigo-400">{{ u.plan_tier }}</td>
            <td class="px-4 py-2.5 text-right font-mono font-semibold text-emerald-600 dark:text-emerald-400">${{ u.balance_usd }}</td>
          </tr>
          {% empty %}
          <tr><td colspan="4" class="px-4 py-6 text-center text-slate-500">No users in database yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </section>

  <section class="glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
    <div class="px-4 sm:px-6 py-3.5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
      <h3 class="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
        <i data-lucide="receipt" class="w-4 h-4 text-emerald-500"></i> Recent Transactions (`tblinc_billing_transactions`)
      </h3>
      <a href="{{ admin_prefix }}/billingtransaction/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">View all &rarr;</a>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-100 dark:bg-slate-900/90 uppercase text-slate-500 border-b border-slate-200 dark:border-slate-800">
          <tr>
            <th class="px-4 py-2.5">Ref</th>
            <th class="px-4 py-2.5">User</th>
            <th class="px-4 py-2.5">Type</th>
            <th class="px-4 py-2.5 text-right">Amount</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
          {% for tx in recent_transactions %}
          <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/30">
            <td class="px-4 py-2.5 font-mono text-slate-500">
              <a href="{{ admin_prefix }}/billingtransaction/{{ tx.id }}/edit/" class="hover:text-indigo-500">{{ tx.reference_id }}</a>
            </td>
            <td class="px-4 py-2.5 font-semibold text-slate-800 dark:text-slate-200">{{ tx.username }}</td>
            <td class="px-4 py-2.5 uppercase font-mono text-slate-500">{{ tx.tx_type }}</td>
            <td class="px-4 py-2.5 text-right font-mono font-semibold text-slate-900 dark:text-white">${{ tx.amount_usd }}</td>
          </tr>
          {% empty %}
          <tr><td colspan="4" class="px-4 py-6 text-center text-slate-500">No transactions in database yet.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </section>
</div>
{% endblock %}
"""

ADMIN_LIST = """{% extends "tblinc_admin_base.html" %}
{% block title %}{{ model_plural }} · {{ admin_title }}{% endblock %}
{% block header_title %}{{ model_plural }}{% endblock %}
{% block admin_content %}
<div class="w-full flex flex-col sm:flex-row sm:items-center justify-between gap-3">
  <form method="get" class="w-full sm:flex-1 sm:max-w-lg flex items-center gap-2">
    <div class="relative flex-1">
      <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3.5 top-3"></i>
      <input type="text" name="q" value="{{ search_query }}" placeholder="Search {{ model_plural }}..." class="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500">
    </div>
    <button type="submit" class="px-4 py-2.5 rounded-xl bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-sm font-medium text-slate-800 dark:text-slate-200 transition">Search</button>
  </form>
  <a href="{{ admin_prefix }}/{{ model_slug }}/create/" class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/25 transition">
    <i data-lucide="plus-circle" class="w-4 h-4"></i>
    <span>Add {{ model_name }}</span>
  </a>
</div>

<div data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[640px] text-left text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          {% for col in columns %}
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">{{ col }}</th>
          {% endfor %}
          <th class="px-4 sm:px-6 py-3.5 text-right font-semibold whitespace-nowrap">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for row in rows %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
          {% for cell in row.cells %}
          <td class="px-4 sm:px-6 py-3.5 text-slate-700 dark:text-slate-200 max-w-[240px] lg:max-w-md xl:max-w-xl truncate">{{ cell }}</td>
          {% endfor %}
          <td class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap space-x-2">
            <a href="{{ admin_prefix }}/{{ model_slug }}/{{ row.pk }}/edit/" class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-indigo-50 dark:bg-slate-800 hover:bg-indigo-100 dark:hover:bg-indigo-600/30 text-indigo-700 dark:text-indigo-300 text-xs font-medium transition">
              <i data-lucide="pencil" class="w-3.5 h-3.5"></i> Edit
            </a>
            <a href="{{ admin_prefix }}/{{ model_slug }}/{{ row.pk }}/delete/" class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-rose-50 dark:bg-slate-800 hover:bg-rose-100 dark:hover:bg-rose-600/30 text-rose-700 dark:text-rose-300 text-xs font-medium transition">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i> Delete
            </a>
          </td>
        </tr>
        {% empty %}
        <tr>
          <td colspan="100" class="px-6 py-12 text-center text-slate-500 dark:text-slate-400">No {{ model_plural }} found.</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  <div class="px-4 sm:px-6 py-3 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-slate-500 dark:text-slate-400">
    <span>Showing {{ rows|length }} of {{ total_count }} records (Page {{ page }} / {{ total_pages }})</span>
    <div class="flex items-center gap-2">
      {% if has_prev %}
      <a href="?page={{ prev_page }}&q={{ search_query }}" class="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200">Previous</a>
      {% endif %}
      {% if has_next %}
      <a href="?page={{ next_page }}&q={{ search_query }}" class="px-3 py-1.5 rounded-lg bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200">Next</a>
      {% endif %}
    </div>
  </div>
</div>
{% endblock %}
"""

ADMIN_FORM = """{% extends "tblinc_admin_base.html" %}
{% block title %}{{ action }} {{ model_name }} · {{ admin_title }}{% endblock %}
{% block header_title %}{{ action }} {{ model_name }}{% endblock %}
{% block admin_content %}
<div data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-6 shadow-sm">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-4">
    <div>
      <h2 class="text-base font-semibold text-slate-900 dark:text-white">{{ action }} {{ model_name }}</h2>
      <p class="text-xs text-slate-500 dark:text-slate-400">Auto-generated ModelForm with CSRF protection and field validation</p>
    </div>
    <a href="{{ admin_prefix }}/{{ model_slug }}/" class="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white inline-flex items-center gap-1">
      <i data-lucide="arrow-left" class="w-3.5 h-3.5"></i> Back to list
    </a>
  </div>
  <form method="post" class="space-y-4">
    {% csrf_token %}
    {{ form_html|safe }}
    <div class="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col-reverse sm:flex-row sm:items-center justify-end gap-3">
      <a href="{{ admin_prefix }}/{{ model_slug }}/" class="w-full sm:w-auto text-center px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition">Cancel</a>
      <button type="submit" class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/25 transition">
        <i data-lucide="save" class="w-4 h-4"></i>
        <span>Save {{ model_name }}</span>
      </button>
    </div>
  </form>
</div>
{% endblock %}
"""

ADMIN_DELETE = """{% extends "tblinc_admin_base.html" %}
{% block title %}Delete {{ model_name }} · {{ admin_title }}{% endblock %}
{% block header_title %}Confirm Deletion{% endblock %}
{% block admin_content %}
<div data-motion="card" class="max-w-lg glass border border-rose-300 dark:border-rose-500/30 rounded-2xl p-5 sm:p-6 space-y-5 shadow-sm">
  <div class="flex items-start gap-3">
    <div class="h-10 w-10 rounded-xl bg-rose-100 dark:bg-rose-500/20 text-rose-600 dark:text-rose-400 flex items-center justify-center shrink-0">
      <i data-lucide="alert-triangle" class="w-5 h-5"></i>
    </div>
    <div>
      <h2 class="text-base font-semibold text-slate-900 dark:text-white">Delete {{ model_name }} #{{ object_pk }}?</h2>
      <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">You are about to permanently remove <strong class="text-slate-900 dark:text-slate-200">{{ object_str }}</strong>. This action cannot be undone.</p>
    </div>
  </div>
  <form method="post" class="flex flex-col-reverse sm:flex-row sm:items-center justify-end gap-3 pt-2">
    {% csrf_token %}
    <a href="{{ admin_prefix }}/{{ model_slug }}/" class="w-full sm:w-auto text-center px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition">Cancel</a>
    <button type="submit" class="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-sm font-semibold transition">
      <i data-lucide="trash-2" class="w-4 h-4"></i> Delete Permanently
    </button>
  </form>
</div>
{% endblock %}
"""

AI_STUDIO_PANEL = """<!-- Full Multimedia tblinc AI: Chat · Images · Video · Audio · Music · All 25 Models -->
<section id="tblinc-ai-studio" class="space-y-5">
  <!-- Studio Tab Bar (PC / Tablet / Mobile scrollable) -->
  <div class="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1" role="tablist">
    <button type="button" data-studio-tab="chat" onclick="tblincStudioTab('chat')" class="studio-tab shrink-0 min-h-[42px] inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition bg-indigo-600 text-white border-indigo-600 shadow-sm">
      <i data-lucide="message-square" class="w-4 h-4"></i><span>AI Chat</span>
    </button>
    <button type="button" data-studio-tab="images" onclick="tblincStudioTab('images')" class="studio-tab shrink-0 min-h-[42px] inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-800 hover:border-indigo-400">
      <i data-lucide="image" class="w-4 h-4 text-pink-500"></i><span>AI Images</span>
    </button>
    <button type="button" data-studio-tab="video" onclick="tblincStudioTab('video')" class="studio-tab shrink-0 min-h-[42px] inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-800 hover:border-indigo-400">
      <i data-lucide="film" class="w-4 h-4 text-cyan-500"></i><span>AI Video</span>
    </button>
    <button type="button" data-studio-tab="audio" onclick="tblincStudioTab('audio')" class="studio-tab shrink-0 min-h-[42px] inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-800 hover:border-indigo-400">
      <i data-lucide="mic" class="w-4 h-4 text-emerald-500"></i><span>AI Audio</span>
    </button>
    <button type="button" data-studio-tab="music" onclick="tblincStudioTab('music')" class="studio-tab shrink-0 min-h-[42px] inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold border transition bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-800 hover:border-indigo-400">
      <i data-lucide="music" class="w-4 h-4 text-amber-500"></i><span>AI Music</span>
    </button>
  </div>

  <!-- 1. AI CHAT TAB -->
  <div data-studio-pane="chat" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 space-y-4 shadow-sm">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
      <div>
        <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <i data-lucide="message-square-text" class="w-5 h-5 text-indigo-500"></i> Conversational AI Chat
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400">Powered by AI Text &amp; Chat Model + Knowledge Search (RAG) + Sentiment Analyzer</p>
      </div>
      <select id="studio-chat-mode" class="rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs font-medium text-slate-800 dark:text-slate-200">
        <option value="assistant">Smart Assistant (Docs + AI)</option>
        <option value="rag">Knowledge Search Only</option>
        <option value="creative">Creative AI Writer</option>
      </select>
    </div>
    <div id="studio-chat-log" class="h-72 sm:h-80 overflow-y-auto rounded-2xl bg-slate-100/80 dark:bg-slate-950/80 border border-slate-200 dark:border-slate-800 p-4 space-y-3 text-sm">
      <div class="flex items-start gap-2.5">
        <span class="h-8 w-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0"><i data-lucide="bot" class="w-4 h-4"></i></span>
        <div class="rounded-2xl rounded-tl-none bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2.5 text-slate-700 dark:text-slate-200 max-w-2xl shadow-sm">
          Hello! Ask me anything about <strong>tblinc</strong>, AI models, admin panels, or switch tabs above to generate live <strong>Images</strong>, <strong>Video</strong>, <strong>Voice Audio</strong>, and <strong>Music</strong>.
        </div>
      </div>
    </div>
    <div class="flex flex-wrap gap-2">
      <button type="button" onclick="tblincQuickChat('How does tblinc generate an admin panel?')" class="text-xs px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 transition">Admin panel guide</button>
      <button type="button" onclick="tblincQuickChat('What AI models are built into tblinc?')" class="text-xs px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 transition">Built-in AI models</button>
      <button type="button" onclick="tblincQuickChat('artificial intelligence builds fast modular systems')" class="text-xs px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-indigo-100 dark:hover:bg-indigo-500/20 transition">Creative continuation</button>
    </div>
    <form onsubmit="event.preventDefault(); tblincSendChat();" class="flex flex-col sm:flex-row gap-2">
      <input id="studio-chat-input" type="text" placeholder="Type a message to tblinc AI..." class="flex-1 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-4 py-2.5 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
      <button type="submit" class="min-h-[44px] px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold inline-flex items-center justify-center gap-2 shadow-sm transition">
        <i data-lucide="send" class="w-4 h-4"></i> Send
      </button>
    </form>
  </div>

  <!-- 2. AI IMAGES TAB -->
  <div data-studio-pane="images" class="hidden glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 space-y-5 shadow-sm">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div class="lg:col-span-5 space-y-4">
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <i data-lucide="sparkles" class="w-5 h-5 text-pink-500"></i> AI Image Generator
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Reverse-diffusion sampling with classifier-free guidance &amp; live visual export.</p>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Prompt</label>
            <input id="studio-img-prompt" type="text" value="neon star nebula" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100">
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Style Palette</label>
              <select id="studio-img-style" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
                <option value="neon">Neon Cyber</option>
                <option value="sunset">Warm Sunset</option>
                <option value="aurora">Aurora Glow</option>
                <option value="ocean">Deep Ocean</option>
                <option value="minimal">Minimal Mono</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Seed</label>
              <input id="studio-img-seed" type="number" value="42" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100">
            </div>
          </div>
          <div class="flex flex-col sm:flex-row gap-2 pt-1">
            <button type="button" onclick="tblincGenImage()" class="flex-1 min-h-[44px] px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white text-sm font-semibold inline-flex items-center justify-center gap-2 shadow transition">
              <i data-lucide="wand-2" class="w-4 h-4"></i> Generate Image
            </button>
            <a id="studio-img-dl" download="tblinc-ai-image.svg" href="#" class="hidden min-h-[44px] px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium inline-flex items-center justify-center gap-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
              <i data-lucide="download" class="w-4 h-4"></i> Download
            </a>
          </div>
          <p id="studio-img-meta" class="text-xs text-slate-500 dark:text-slate-400"></p>
        </div>
      </div>
      <div class="lg:col-span-7">
        <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-950 overflow-hidden aspect-[16/10] flex items-center justify-center">
          <img id="studio-img-preview" alt="Generated AI image" class="hidden w-full h-full object-cover" />
          <div id="studio-img-empty" class="text-center p-6 text-xs text-slate-500 dark:text-slate-400 space-y-2">
            <i data-lucide="image" class="w-10 h-10 mx-auto text-slate-400"></i>
            <p>Click <strong>Generate Image</strong> to synthesize a diffused visual artwork.</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 3. AI VIDEO TAB -->
  <div data-studio-pane="video" class="hidden glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 space-y-5 shadow-sm">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div class="lg:col-span-5 space-y-4">
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <i data-lucide="clapperboard" class="w-5 h-5 text-cyan-500"></i> AI Video Generator &amp; Motion Analyzer
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Synthesizes animated multi-frame AI clips and classifies temporal optical flow.</p>
        </div>
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Scene Prompt</label>
            <input id="studio-vid-prompt" type="text" value="luminous orbital plasma wave" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100">
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Motion Style</label>
              <select id="studio-vid-motion" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
                <option value="pan_right">Pan Right</option>
                <option value="pan_left">Pan Left</option>
                <option value="zoom_in">Zoom In</option>
                <option value="orbit">360 Orbit</option>
                <option value="static">Static Pulse</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Frames</label>
              <input id="studio-vid-frames" type="number" value="30" min="8" max="60" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100">
            </div>
          </div>
          <div class="flex flex-col sm:flex-row gap-2">
            <button type="button" onclick="tblincGenVideo()" class="flex-1 min-h-[44px] px-4 py-2.5 rounded-xl bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-sm font-semibold inline-flex items-center justify-center gap-2 shadow transition">
              <i data-lucide="film" class="w-4 h-4"></i> Generate Video
            </button>
            <button type="button" onclick="tblincToggleVideoPlay()" id="studio-vid-playbtn" class="min-h-[44px] px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium inline-flex items-center justify-center gap-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
              <i data-lucide="pause" class="w-4 h-4"></i> Play/Pause
            </button>
          </div>
          <p id="studio-vid-meta" class="text-xs text-slate-500 dark:text-slate-400"></p>
        </div>
      </div>
      <div class="lg:col-span-7 space-y-2">
        <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-950 overflow-hidden aspect-[16/10] relative">
          <canvas id="studio-vid-canvas" width="640" height="400" class="w-full h-full block"></canvas>
          <span id="studio-vid-badge" class="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-slate-900/80 text-cyan-300 font-mono text-[11px] border border-cyan-500/30">Ready · Click Generate Video</span>
        </div>
      </div>
    </div>
  </div>

  <!-- 4. AI AUDIO / VOICE TAB -->
  <div data-studio-pane="audio" class="hidden glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 space-y-5 shadow-sm">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div class="lg:col-span-6 space-y-4">
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <i data-lucide="mic" class="w-5 h-5 text-emerald-500"></i> AI Voice &amp; Audio Synthesizer (TTS + DFT)
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Generates real playable 16-bit PCM WAV voice audio with spectral DFT analysis.</p>
        </div>
        <textarea id="studio-aud-text" rows="3" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 p-3.5 text-sm text-slate-900 dark:text-slate-100">Welcome to tblinc AI studio. Build voice, music, video, images, and chat in pure Python.</textarea>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Voice</label>
            <select id="studio-aud-voice" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
              <option value="neutral">Neutral</option>
              <option value="warm">Warm Deep</option>
              <option value="bright">Bright Clear</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Pitch (Hz)</label>
            <input id="studio-aud-pitch" type="number" value="165" min="80" max="420" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Speed</label>
            <input id="studio-aud-speed" type="number" step="0.1" value="1.0" min="0.5" max="2.0" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-2">
          <button type="button" onclick="tblincGenAudio()" class="flex-1 min-h-[44px] px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold inline-flex items-center justify-center gap-2 shadow transition">
            <i data-lucide="volume-2" class="w-4 h-4"></i> Synthesize Voice WAV
          </button>
          <a id="studio-aud-dl" download="tblinc-voice.wav" href="#" class="hidden min-h-[44px] px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium inline-flex items-center justify-center gap-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
            <i data-lucide="download" class="w-4 h-4"></i> Download WAV
          </a>
        </div>
      </div>
      <div class="lg:col-span-6 space-y-4">
        <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-950 p-5 space-y-4">
          <div id="studio-aud-bars" class="h-24 flex items-end justify-between gap-1 px-2"></div>
          <audio id="studio-aud-player" controls class="w-full"></audio>
          <p id="studio-aud-meta" class="text-xs text-slate-500 dark:text-slate-400">Click <strong>Synthesize Voice WAV</strong> to generate and play audio.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- 5. AI MUSIC TAB -->
  <div data-studio-pane="music" class="hidden glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-6 space-y-5 shadow-sm">
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div class="lg:col-span-6 space-y-4">
        <div>
          <h2 class="text-base sm:text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <i data-lucide="music" class="w-5 h-5 text-amber-500"></i> Polyphonic AI Music Composer
          </h2>
          <p class="text-xs text-slate-500 dark:text-slate-400">Composes chord progressions, basslines, drums &amp; lead melodies into playable 16kHz WAV tracks.</p>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Genre / Mood</label>
            <select id="studio-mus-mood" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
              <option value="synthwave">Synthwave (Am · 112 BPM)</option>
              <option value="lofi">Lo-Fi Chill (Cmaj7 · 82 BPM)</option>
              <option value="ambient">Ambient Space (D Lydian · 72 BPM)</option>
              <option value="cinematic">Cinematic Epic (Dm · 96 BPM)</option>
              <option value="energetic">Energetic Pulse (Em · 128 BPM)</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Tempo (BPM)</label>
            <input id="studio-mus-bpm" type="number" value="112" min="60" max="180" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Duration (sec)</label>
            <input id="studio-mus-dur" type="number" value="5" min="2" max="10" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
          </div>
          <div>
            <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Seed</label>
            <input id="studio-mus-seed" type="number" value="42" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
          </div>
        </div>
        <div class="flex flex-col sm:flex-row gap-2">
          <button type="button" onclick="tblincGenMusic()" class="flex-1 min-h-[44px] px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-rose-600 hover:from-amber-400 hover:to-rose-500 text-white text-sm font-semibold inline-flex items-center justify-center gap-2 shadow transition">
            <i data-lucide="disc-3" class="w-4 h-4"></i> Compose AI Music Track
          </button>
          <a id="studio-mus-dl" download="tblinc-ai-music.wav" href="#" class="hidden min-h-[44px] px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium inline-flex items-center justify-center gap-1.5 hover:bg-slate-100 dark:hover:bg-slate-800">
            <i data-lucide="download" class="w-4 h-4"></i> Download WAV
          </a>
        </div>
      </div>
      <div class="lg:col-span-6 space-y-4">
        <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-slate-950 p-5 space-y-4">
          <div id="studio-mus-bars" class="h-24 flex items-end justify-between gap-1 px-2"></div>
          <audio id="studio-mus-player" controls class="w-full"></audio>
          <div id="studio-mus-chords" class="flex flex-wrap gap-1.5"></div>
          <p id="studio-mus-meta" class="text-xs text-slate-500 dark:text-slate-400">Click <strong>Compose AI Music Track</strong> to synthesize and play a polyphonic WAV.</p>
        </div>
      </div>
    </div>
  </div>
</section>
"""

AI_STUDIO_JS = """<script>
window.tblincStudioTab = function (name) {
  if (window.tblincHighlightSidenavTab) { window.tblincHighlightSidenavTab(name); }
  document.querySelectorAll("[data-studio-pane]").forEach((p) => {
    p.classList.toggle("hidden", p.dataset.studioPane !== name);
  });
  document.querySelectorAll("[data-studio-tab]").forEach((btn) => {
    const active = btn.dataset.studioTab === name;
    btn.classList.toggle("bg-indigo-600", active);
    btn.classList.toggle("text-white", active);
    btn.classList.toggle("border-indigo-600", active);
    btn.classList.toggle("bg-white", !active);
    btn.classList.toggle("dark:bg-slate-900", !active);
    btn.classList.toggle("text-slate-700", !active);
    btn.classList.toggle("dark:text-slate-200", !active);
    btn.classList.toggle("border-slate-200", !active);
    btn.classList.toggle("dark:border-slate-800", !active);
  });
};

window.tblincStudioFilter = function (q) {
  const needle = (q || "").trim().toLowerCase();
  document.querySelectorAll("[data-studio-card]").forEach((c) => {
    c.classList.toggle("hidden", Boolean(needle) && !(c.dataset.search || "").toLowerCase().includes(needle));
  });
};

function tblincRenderBars(containerId, bars, colorCls) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = (bars || []).map((v) => {
    const h = Math.max(8, Math.round(v * 92));
    return '<div class="flex-1 rounded-full ' + colorCls + '" style="height:' + h + '%"></div>';
  }).join("");
}

function tblincAiHeaders() {
  const h = { "Content-Type": "application/json" };
  try {
    const k = (localStorage.getItem("tblinc-user-api-key") || "").trim();
    if (k) { h["X-API-Key"] = k; }
  } catch (e) {}
  return h;
}

window.tblincQuickChat = function (text) {
  const inp = document.getElementById("studio-chat-input");
  if (inp) { inp.value = text; }
  window.tblincSendChat();
};

window.tblincSendChat = async function () {
  const inp = document.getElementById("studio-chat-input");
  const log = document.getElementById("studio-chat-log");
  const mode = (document.getElementById("studio-chat-mode") || {}).value || "assistant";
  const msg = (inp.value || "").trim();
  if (!msg) return;
  inp.value = "";
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  log.insertAdjacentHTML("beforeend",
    '<div class="flex justify-end"><div class="rounded-2xl rounded-tr-none bg-indigo-600 text-white px-4 py-2.5 max-w-xl shadow-sm">' + esc(msg) + '</div></div>'
  );
  log.scrollTop = log.scrollHeight;
  try {
    const resp = await fetch("/api/ai/chat", {
      method: "POST",
      headers: tblincAiHeaders(),
      body: JSON.stringify({ message: msg, mode })
    });
    const data = await resp.json();
    if (!resp.ok) {
      log.insertAdjacentHTML("beforeend", '<div class="text-xs text-rose-500">Error: ' + esc(data.error || ("HTTP " + resp.status)) + '</div>');
      log.scrollTop = log.scrollHeight;
      return;
    }
    log.insertAdjacentHTML("beforeend",
      '<div class="flex items-start gap-2.5"><span class="h-8 w-8 rounded-xl bg-cyan-600 text-white flex items-center justify-center shrink-0 text-xs font-bold">AI</span>' +
      '<div class="rounded-2xl rounded-tl-none bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-4 py-2.5 text-slate-800 dark:text-slate-100 max-w-2xl shadow-sm">' +
      '<div>' + esc(data.reply || "") + '</div>' +
      '<div class="mt-1.5 text-[10px] font-mono text-slate-400">source=' + esc(data.source || "ai") + ' · sentiment=' + esc(data.sentiment || "neutral") + ' · ' + (data.latency_ms || 0) + 'ms</div>' +
      '</div></div>'
    );
    log.scrollTop = log.scrollHeight;
  } catch (err) {
    log.insertAdjacentHTML("beforeend", '<div class="text-xs text-rose-500">Error: ' + esc(err.message) + '</div>');
  }
};

window.tblincGenImage = async function () {
  const prompt = document.getElementById("studio-img-prompt").value;
  const style = document.getElementById("studio-img-style").value;
  const seed = parseInt(document.getElementById("studio-img-seed").value || "42", 10);
  const meta = document.getElementById("studio-img-meta");
  meta.textContent = "Generating diffused image...";
  try {
    const resp = await fetch("/api/ai/image", {
      method: "POST",
      headers: tblincAiHeaders(),
      body: JSON.stringify({ prompt, style, seed })
    });
    const data = await resp.json();
    if (!resp.ok) { meta.textContent = "Error: " + (data.error || resp.status); return; }
    const details = (data.result && data.result.details) || {};
    const img = document.getElementById("studio-img-preview");
    const empty = document.getElementById("studio-img-empty");
    const dl = document.getElementById("studio-img-dl");
    if (details.image_data_uri) {
      img.src = details.image_data_uri;
      img.classList.remove("hidden");
      if (empty) empty.classList.add("hidden");
      if (dl) { dl.href = details.image_data_uri; dl.classList.remove("hidden"); }
    }
    meta.textContent = "Concept: " + (details.matched_concept || prompt) + " · Style: " + style + " · Fidelity: " + (data.result ? data.result.confidence : 1) + " · " + (data.elapsed_ms || 0) + "ms";
  } catch (err) {
    meta.textContent = "Error: " + err.message;
  }
};

window.__tblincVidState = { frames: [], fps: 12, idx: 0, playing: false, timer: null, prompt: "" };
function tblincDrawVidFrame() {
  const st = window.__tblincVidState;
  const canvas = document.getElementById("studio-vid-canvas");
  if (!canvas || !st.frames.length) return;
  const ctx = canvas.getContext("2d");
  const f = st.frames[st.idx % st.frames.length];
  const w = canvas.width, h = canvas.height;
  const grad = ctx.createLinearGradient(0, 0, w, h);
  grad.addColorStop(0, "hsl(" + f.hue + ", 65%, 10%)");
  grad.addColorStop(1, "hsl(" + ((f.hue + 60) % 360) + ", 70%, 18%)");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, w, h);

  // Luminous motion waves
  for (let k = 0; k < 3; k++) {
    ctx.beginPath();
    ctx.strokeStyle = "hsla(" + ((f.hue + k * 45) % 360) + ", 90%, 65%, 0.35)";
    ctx.lineWidth = 2.5;
    for (let x = 0; x <= w; x += 16) {
      const y = h * 0.5 + Math.sin(x * 0.015 + st.idx * 0.35 + k * 1.4) * (34 + k * 16);
      if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  const cx = f.cx * w, cy = f.cy * h, rad = f.radius * Math.min(w, h);
  const orb = ctx.createRadialGradient(cx, cy, 4, cx, cy, rad * 1.4);
  orb.addColorStop(0, "hsla(" + ((f.hue + 30) % 360) + ", 100%, 78%, 0.95)");
  orb.addColorStop(0.55, "hsla(" + f.hue + ", 90%, 55%, 0.45)");
  orb.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = orb;
  ctx.beginPath();
  ctx.arc(cx, cy, rad * 1.4, 0, Math.PI * 2);
  ctx.fill();

  const badge = document.getElementById("studio-vid-badge");
  if (badge) {
    badge.textContent = "Frame " + (st.idx + 1) + "/" + st.frames.length + " · " + st.fps + " FPS · " + st.prompt;
  }
  st.idx = (st.idx + 1) % st.frames.length;
}

window.tblincToggleVideoPlay = function () {
  const st = window.__tblincVidState;
  if (!st.frames.length) return;
  st.playing = !st.playing;
  clearInterval(st.timer);
  if (st.playing) {
    st.timer = setInterval(tblincDrawVidFrame, Math.round(1000 / st.fps));
  }
};

window.tblincGenVideo = async function () {
  const prompt = document.getElementById("studio-vid-prompt").value;
  const motion = document.getElementById("studio-vid-motion").value;
  const frames = parseInt(document.getElementById("studio-vid-frames").value || "30", 10);
  const meta = document.getElementById("studio-vid-meta");
  meta.textContent = "Generating multi-frame AI video...";
  try {
    const resp = await fetch("/api/ai/video", {
      method: "POST",
      headers: tblincAiHeaders(),
      body: JSON.stringify({ prompt, motion, frames, fps: 14 })
    });
    const data = await resp.json();
    if (!resp.ok) { meta.textContent = "Error: " + (data.error || resp.status); return; }
    const st = window.__tblincVidState;
    clearInterval(st.timer);
    st.frames = data.keyframes || [];
    st.fps = data.fps || 14;
    st.idx = 0;
    st.prompt = data.prompt || prompt;
    st.playing = true;
    tblincDrawVidFrame();
    st.timer = setInterval(tblincDrawVidFrame, Math.round(1000 / st.fps));
    const pred = data.analysis ? data.analysis.prediction : motion;
    meta.textContent = "Motion detected: " + pred + " · " + data.num_frames + " frames (" + data.duration_sec + "s) · " + data.latency_ms + "ms";
  } catch (err) {
    meta.textContent = "Error: " + err.message;
  }
};

window.tblincGenAudio = async function () {
  const text = document.getElementById("studio-aud-text").value;
  const voice = document.getElementById("studio-aud-voice").value;
  const pitch_hz = parseFloat(document.getElementById("studio-aud-pitch").value || "165");
  const speed = parseFloat(document.getElementById("studio-aud-speed").value || "1.0");
  const meta = document.getElementById("studio-aud-meta");
  meta.textContent = "Synthesizing PCM WAV speech...";
  try {
    const resp = await fetch("/api/ai/audio", {
      method: "POST",
      headers: tblincAiHeaders(),
      body: JSON.stringify({ text, voice, pitch_hz, speed })
    });
    const data = await resp.json();
    if (!resp.ok) { meta.textContent = "Error: " + (data.error || resp.status); return; }
    const details = (data.result && data.result.details) || {};
    const player = document.getElementById("studio-aud-player");
    const dl = document.getElementById("studio-aud-dl");
    if (details.audio_data_uri) {
      player.src = details.audio_data_uri;
      player.load();
      if (dl) { dl.href = details.audio_data_uri; dl.classList.remove("hidden"); }
    }
    tblincRenderBars("studio-aud-bars", details.waveform_bars || [], "bg-emerald-500/80");
    const band = data.spectrum_analysis ? data.spectrum_analysis.prediction : "voice";
    meta.textContent = "Duration: " + details.duration_sec + "s · " + details.wav_bytes_len + " bytes · Acoustic band: " + band;
  } catch (err) {
    meta.textContent = "Error: " + err.message;
  }
};

window.tblincGenMusic = async function () {
  const mood = document.getElementById("studio-mus-mood").value;
  const bpm = parseInt(document.getElementById("studio-mus-bpm").value || "112", 10);
  const duration_sec = parseFloat(document.getElementById("studio-mus-dur").value || "5");
  const seed = parseInt(document.getElementById("studio-mus-seed").value || "42", 10);
  const meta = document.getElementById("studio-mus-meta");
  meta.textContent = "Composing polyphonic WAV track...";
  try {
    const resp = await fetch("/api/ai/music", {
      method: "POST",
      headers: tblincAiHeaders(),
      body: JSON.stringify({ mood, bpm, duration_sec, seed })
    });
    const data = await resp.json();
    if (!resp.ok) { meta.textContent = "Error: " + (data.error || resp.status); return; }
    const details = (data.result && data.result.details) || {};
    const player = document.getElementById("studio-mus-player");
    const dl = document.getElementById("studio-mus-dl");
    if (details.audio_data_uri) {
      player.src = details.audio_data_uri;
      player.load();
      if (dl) { dl.href = details.audio_data_uri; dl.classList.remove("hidden"); }
    }
    tblincRenderBars("studio-mus-bars", details.waveform_bars || [], "bg-amber-500/85");
    const chordsEl = document.getElementById("studio-mus-chords");
    if (chordsEl && details.chords) {
      chordsEl.innerHTML = details.chords.map((c) =>
        '<span class="px-2.5 py-1 rounded-lg text-xs font-mono bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30">' + c + '</span>'
      ).join("");
    }
    meta.textContent = "Mood: " + details.mood + " · " + details.bpm + " BPM · " + details.duration_sec + "s · " + details.wav_bytes_len + " bytes";
  } catch (err) {
    meta.textContent = "Error: " + err.message;
  }
};

async function runAIModel(key) {
  const inpEl = document.getElementById("inp-" + key);
  const outEl = document.getElementById("out-" + key);
  outEl.classList.remove("hidden");
  outEl.textContent = "Running " + key + "...";
  try {
    const payload = inpEl.value.trim() ? JSON.parse(inpEl.value) : null;
    const resp = await fetch("/api/ai/" + encodeURIComponent(key) + "/run", {
      method: "POST",
      headers: tblincAiHeaders(),
      body: JSON.stringify({ input: payload })
    });
    const data = await resp.json();
    outEl.textContent = JSON.stringify(data, null, 2);
    if (window.Motion && window.Motion.animate) {
      window.Motion.animate(outEl, { opacity: [0, 1], y: [6, 0] }, { duration: 0.25 });
    }
  } catch (err) {
    outEl.textContent = "Error: " + err.message;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    const prefTab = localStorage.getItem("tblinc-default-tab");
    if (prefTab && ["chat", "images", "video", "audio", "music"].includes(prefTab) && document.querySelector("[data-studio-pane]")) {
      window.tblincStudioTab(prefTab);
    }
  } catch (e) {}
});
</script>
"""

ADMIN_AI_STUDIO = """{% extends "tblinc_admin_base.html" %}
{% block title %}tblinc AI · {{ admin_title }}{% endblock %}
{% block header_title %}tblinc AI — Chat · Images · Video · Audio · Music{% endblock %}
{% block admin_content %}
{% include "tblinc_ai_studio_panel.html" %}
{% endblock %}
{% block scripts %}
{% include "tblinc_ai_studio_js.html" %}
{% endblock %}
"""

ADMIN_MODEL_HUB = """{% extends "tblinc_admin_base.html" %}
{% block title %}AI Model Hub ({{ ai_model_count }}) · {{ admin_title }}{% endblock %}
{% block header_title %}AI Model Hub ({{ ai_model_count }}){% endblock %}
{% block admin_content %}
<div class="space-y-4">
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
    <div class="relative w-full md:max-w-md">
      <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3.5 top-3"></i>
      <input type="search" oninput="tblincStudioFilter(this.value)" placeholder="Search all {{ ai_model_count }} built-in AI models..." class="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500">
    </div>
    <div class="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
      <a href="{{ admin_prefix }}/models/" class="shrink-0 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:border-indigo-400">All</a>
      {% for cat in categories %}
      <a href="{{ admin_prefix }}/models/?category={{ cat }}" class="shrink-0 px-3 py-1.5 rounded-xl text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:border-indigo-400">{{ cat }}</a>
      {% endfor %}
    </div>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
    {% for m in ai_models %}
    <div data-motion="card" data-studio-card data-search="{{ m.name }} {{ m.key }} {{ m.category }} {{ m.task }}" class="glass border border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-indigo-500/40 rounded-2xl p-4 sm:p-5 flex flex-col justify-between transition shadow-sm">
      <div>
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 truncate">{{ m.category }}</span>
          <code class="text-[11px] text-slate-500 dark:text-slate-400 shrink-0">{{ m.key }}</code>
        </div>
        <h3 class="text-base font-bold text-slate-900 dark:text-white">{{ m.name }}</h3>
        <p class="text-xs text-cyan-700 dark:text-cyan-300/90 mt-0.5">{{ m.task }}</p>
        <p class="text-xs text-slate-600 dark:text-slate-400 mt-2 leading-relaxed">{{ m.description }}</p>
      </div>
      <div class="mt-4 pt-4 border-t border-slate-200 dark:border-slate-800/80 space-y-2.5">
        <textarea id="inp-{{ m.key }}" rows="2" class="w-full rounded-xl bg-slate-100 dark:bg-slate-950/90 border border-slate-300 dark:border-slate-700/80 p-2.5 font-mono text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500">{{ m.input_json }}</textarea>
        <button onclick="runAIModel('{{ m.key }}')" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-semibold shadow transition">
          <i data-lucide="play" class="w-3.5 h-3.5"></i> Run Live Train &amp; Predict
        </button>
        <pre id="out-{{ m.key }}" class="hidden rounded-xl bg-slate-900 dark:bg-slate-950 border border-emerald-500/30 p-3 text-[11px] text-emerald-300 overflow-x-auto max-h-48"></pre>
      </div>
    </div>
    {% endfor %}
  </div>
</div>
{% endblock %}
{% block scripts %}
{% include "tblinc_ai_studio_js.html" %}
{% endblock %}
"""

ADMIN_TRAIN = """{% extends "tblinc_admin_base.html" %}
{% block title %}Train AI Models · {{ admin_title }}{% endblock %}
{% block header_title %}Admin AI Training Center{% endblock %}
{% block admin_content %}
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
  <!-- Left: Custom Dataset & Hyperparameters Trainer -->
  <section data-motion="card" class="lg:col-span-6 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <div class="flex items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-4">
      <div>
        <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <i data-lucide="flame" class="w-5 h-5 text-amber-500"></i> Train &amp; Save Custom AI Model
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400">Fits any of the {{ ai_model_count }} built-in models, persists JSON weights, and logs ORM metrics.</p>
      </div>
      <span class="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-cyan-50 dark:bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/30 uppercase shrink-0">{{ hardware.preferred_device }}</span>
    </div>

    <div class="space-y-3.5">
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Run Name</label>
        <input id="train-run-name" type="text" value="Custom Sentiment Model v1" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3.5 py-2.5 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">AI Model</label>
          <select id="train-model-key" onchange="tblincLoadTrainPreset(this.value)" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
            {% for m in ai_models %}
            <option value="{{ m.key }}">{{ m.name }} ({{ m.key }})</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Target Device</label>
          <select id="train-device" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100">
            <option value="auto">Auto ({{ hardware.preferred_device }})</option>
            <option value="cpu">CPU ({{ hardware.cpu_cores }} cores)</option>
            <option value="cuda">NVIDIA CUDA</option>
            <option value="xpu">Intel XPU</option>
          </select>
        </div>
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Hyperparameters (JSON)</label>
        <textarea id="train-hp" rows="3" class="w-full rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 p-3 font-mono text-xs text-slate-800 dark:text-slate-200">{}</textarea>
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Training Dataset (JSON — leave {} for built-in dataset)</label>
        <textarea id="train-dataset" rows="7" class="w-full rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 p-3 font-mono text-xs text-slate-800 dark:text-slate-200">{}</textarea>
      </div>
      <button type="button" onclick="tblincStartTraining()" id="train-start-btn" class="w-full min-h-[44px] inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg transition">
        <i data-lucide="play" class="w-4 h-4"></i> Start Training &amp; Save Weights
      </button>
    </div>
  </section>

  <!-- Right: Live Training Result + Test Saved Artifact -->
  <section class="lg:col-span-6 space-y-5">
    <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
      <div class="flex items-center justify-between">
        <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <i data-lucide="activity" class="w-5 h-5 text-emerald-500"></i> Live Training Telemetry
        </h2>
        <span id="train-status-badge" class="text-[11px] font-mono px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">Idle</span>
      </div>
      <pre id="train-output" class="rounded-xl bg-slate-900 dark:bg-slate-950 border border-slate-700 p-3.5 text-xs text-emerald-300 overflow-x-auto max-h-56">Select a model and click "Start Training & Save Weights".</pre>
    </div>

    <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-3 shadow-sm">
      <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
        <i data-lucide="flask-conical" class="w-5 h-5 text-cyan-500"></i> Test Trained Weights
      </h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
        <div>
          <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Run ID</label>
          <input id="test-run-id" type="number" placeholder="Run #" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
        </div>
        <div class="sm:col-span-2">
          <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Inference Input (JSON)</label>
          <input id="test-run-input" type="text" value="{}" class="w-full rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 px-3 py-2 font-mono text-xs text-slate-800 dark:text-slate-200">
        </div>
      </div>
      <button type="button" onclick="tblincPredictTrainedRun()" class="w-full min-h-[42px] inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition">
        <i data-lucide="zap" class="w-4 h-4"></i> Load Artifact &amp; Predict
      </button>
      <img id="test-run-img" alt="Trained image output" class="hidden w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-950" />
      <pre id="test-run-output" class="hidden rounded-xl bg-slate-900 dark:bg-slate-950 border border-cyan-500/30 p-3 text-xs text-cyan-300 overflow-x-auto max-h-48"></pre>
    </div>
  </section>
</div>

<!-- Saved Training Runs History -->
<section data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="history" class="w-4 h-4 text-indigo-500"></i> Saved Training Runs (SQLite ORM)
    </h2>
    <a href="{{ admin_prefix }}/trainingrun/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Manage in ORM Table &rarr;</a>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[640px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">ID</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Run Name</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">AI Model</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Device</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Duration</th>
          <th class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap">Action</th>
        </tr>
      </thead>
      <tbody id="train-runs-tbody" class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for run in training_runs %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <td class="px-4 sm:px-6 py-3.5 font-mono text-slate-500">#{{ run.id }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-semibold text-slate-900 dark:text-white">{{ run.run_name }}</td>
          <td class="px-4 sm:px-6 py-3.5"><code class="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 text-xs">{{ run.model_key }}</code></td>
          <td class="px-4 sm:px-6 py-3.5 uppercase text-xs text-slate-500">{{ run.device }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-emerald-600 dark:text-emerald-400">{{ run.duration_ms }} ms</td>
          <td class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap">
            <button type="button" onclick="tblincSelectTrainedRun({{ run.id }}, '{{ run.model_key }}')" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-indigo-100 dark:hover:bg-indigo-600/30 text-indigo-700 dark:text-indigo-300 text-xs font-medium">Load &amp; Test</button>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="6" class="px-6 py-8 text-center text-xs text-slate-500">No training runs yet. Launch your first run above!</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>
{% endblock %}
{% block scripts %}
<script>
const TBLINC_TRAIN_PRESETS = {{ presets_json|safe }};

window.tblincLoadTrainPreset = function (key) {
  const p = TBLINC_TRAIN_PRESETS[key] || { hyperparams: {}, dataset: {}, test_input: {} };
  document.getElementById("train-run-name").value = "Custom " + key + " run";
  document.getElementById("train-hp").value = JSON.stringify(p.hyperparams || {}, null, 2);
  document.getElementById("train-dataset").value = JSON.stringify(p.dataset || {}, null, 2);
  document.getElementById("test-run-input").value = JSON.stringify(p.test_input || {});
};

window.tblincSelectTrainedRun = function (runId, modelKey) {
  document.getElementById("test-run-id").value = runId;
  const p = TBLINC_TRAIN_PRESETS[modelKey] || { test_input: {} };
  document.getElementById("test-run-input").value = JSON.stringify(p.test_input || {});
  window.tblincPredictTrainedRun();
};

window.tblincStartTraining = async function () {
  const badge = document.getElementById("train-status-badge");
  const out = document.getElementById("train-output");
  const modelKey = document.getElementById("train-model-key").value;
  const runName = document.getElementById("train-run-name").value;
  const device = document.getElementById("train-device").value;
  badge.textContent = "Training...";
  out.textContent = "Training " + modelKey + "...";
  try {
    const hyperparams = JSON.parse(document.getElementById("train-hp").value || "{}");
    const dataset = JSON.parse(document.getElementById("train-dataset").value || "{}");
    const resp = await fetch("/api/ai/train", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_key: modelKey, run_name: runName, device, hyperparams, dataset })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "Training failed");
    badge.textContent = "Completed · " + data.run.duration_ms + "ms";
    out.textContent = JSON.stringify(data.run, null, 2);
    document.getElementById("test-run-id").value = data.run.id;
    const tbody = document.getElementById("train-runs-tbody");
    if (tbody) {
      const r = data.run;
      const rowHtml =
        '<tr class="bg-emerald-50/40 dark:bg-emerald-500/10">' +
        '<td class="px-4 py-3 font-mono text-slate-500">#' + r.id + '</td>' +
        '<td class="px-4 py-3 font-semibold text-slate-900 dark:text-white">' + r.run_name + '</td>' +
        '<td class="px-4 py-3"><code class="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 text-xs">' + r.model_key + '</code></td>' +
        '<td class="px-4 py-3 uppercase text-xs text-slate-500">' + r.device + '</td>' +
        '<td class="px-4 py-3 font-mono text-xs text-emerald-600 dark:text-emerald-400">' + r.duration_ms + ' ms</td>' +
        '<td class="px-4 py-3 text-right"><button type="button" onclick="tblincSelectTrainedRun(' + r.id + ', \\'' + r.model_key + '\\')" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-indigo-700 dark:text-indigo-300 text-xs font-medium">Load &amp; Test</button></td>' +
        '</tr>';
      tbody.insertAdjacentHTML("afterbegin", rowHtml);
    }
  } catch (err) {
    badge.textContent = "Error";
    out.textContent = "Error: " + err.message;
  }
};

window.tblincPredictTrainedRun = async function () {
  const runId = document.getElementById("test-run-id").value;
  const out = document.getElementById("test-run-output");
  const img = document.getElementById("test-run-img");
  if (!runId) return;
  out.classList.remove("hidden");
  if (img) { img.classList.add("hidden"); }
  out.textContent = "Loading saved artifact #" + runId + "...";
  try {
    const inp = JSON.parse(document.getElementById("test-run-input").value || "{}");
    const resp = await fetch("/api/ai/train/" + encodeURIComponent(runId) + "/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input: inp })
    });
    const data = await resp.json();
    const details = (data.result && data.result.details) || {};
    if (img && details.image_data_uri) {
      img.src = details.image_data_uri;
      img.classList.remove("hidden");
    }
    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = "Error: " + err.message;
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const sel = document.getElementById("train-model-key");
  if (sel) {
    sel.value = "sentiment";
    window.tblincLoadTrainPreset(sel.value);
  }
});
</script>
{% endblock %}
"""

ADMIN_KEYS_QUOTAS = """{% extends "tblinc_admin_base.html" %}
{% block title %}API Keys &amp; Token Quotas · {{ admin_title }}{% endblock %}
{% block header_title %}AI Keys &amp; Token Quotas{% endblock %}
{% block admin_content %}
<!-- Summary KPI Cards -->
<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Active AI Keys</span>
      <i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ summary.active_keys }} <span class="text-sm font-normal text-slate-400">/ {{ summary.total_keys }}</span></div>
    <div class="mt-1 text-xs text-slate-500">Gateway &amp; external provider keys</div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Total Tokens Used</span>
      <i data-lucide="gauge" class="w-4 h-4 text-indigo-500"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ summary.total_tokens_used }}</div>
    <div class="mt-1 text-xs text-slate-500">Global Limit: {{ summary.global_token_limit }} (0 = unlimited)</div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Metered AI Requests</span>
      <i data-lucide="activity" class="w-4 h-4 text-cyan-500"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ summary.total_requests }}</div>
    <div class="mt-1 text-xs text-slate-500">Across Chat, Images, Video, Voice, Music &amp; Hub</div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm">
    <div class="flex items-center justify-between text-slate-500 dark:text-slate-400 text-xs font-medium">
      <span>Models Enabled</span>
      <i data-lucide="shield-check" class="w-4 h-4 text-amber-500"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ summary.models_enabled }} / {{ summary.total_models }}</div>
    <div class="mt-1 text-xs text-slate-500">Live Admin kill-switch &amp; token budgets</div>
  </div>
</div>

<!-- Create Key + Update Model Quota Panels -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
  <!-- Create / Generate AI Key -->
  <section data-motion="card" class="lg:col-span-6 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
      <div>
        <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <i data-lucide="key-round" class="w-5 h-5 text-emerald-500"></i> Issue or Store AI Key
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400">Generate a <code>tbl_sk_...</code> API key or save an OpenAI, Anthropic, Gemini, or Hugging Face key.</p>
      </div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Key Name</label>
        <input id="key-name" type="text" value="Production Gateway Key" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Provider</label>
        <select id="key-provider" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
          <option value="tblinc">tblinc API Key (Auto-Generate)</option>
          <option value="openai">OpenAI</option>
          <option value="anthropic">Anthropic Claude</option>
          <option value="gemini">Google Gemini</option>
          <option value="huggingface">Hugging Face</option>
          <option value="custom">Custom / Local Ollama</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">API Key (optional for tblinc)</label>
        <input id="key-secret" type="password" placeholder="Leave blank to auto-generate tbl_sk_..." class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Allowed Models</label>
        <input id="key-models" type="text" value="*" placeholder="* or chat,image,voice,music" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Token Quota (0 = unlimited)</label>
        <input id="key-token-quota" type="number" value="100000" min="0" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Request Quota (0 = unlimited)</label>
        <input id="key-req-quota" type="number" value="1000" min="0" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
    </div>
    <button type="button" onclick="tblincCreateAIKey()" class="w-full min-h-[44px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow transition">
      <i data-lucide="plus-circle" class="w-4 h-4"></i> Generate &amp; Save AI Key
    </button>
    <div id="key-created-banner" class="hidden rounded-xl border border-emerald-400/40 bg-emerald-50 dark:bg-emerald-500/10 p-3.5 text-xs space-y-2">
      <div class="font-semibold text-emerald-700 dark:text-emerald-300">Key Created — copy it now (shown once):</div>
      <div class="flex items-center gap-2">
        <code id="key-created-val" class="flex-1 break-all font-mono text-slate-900 dark:text-white bg-white/80 dark:bg-slate-950 px-2.5 py-1.5 rounded-lg border border-emerald-300 dark:border-emerald-500/30"></code>
        <button type="button" onclick="navigator.clipboard && navigator.clipboard.writeText(document.getElementById('key-created-val').textContent)" class="px-3 py-1.5 rounded-lg bg-emerald-600 text-white font-semibold shrink-0">Copy</button>
      </div>
      <div class="text-[11px] text-slate-600 dark:text-slate-400">Use header: <code>Authorization: Bearer &lt;key&gt;</code> or <code>X-API-Key: &lt;key&gt;</code></div>
    </div>
  </section>

  <!-- Configure Per-Model Token Quota -->
  <section data-motion="card" class="lg:col-span-6 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
      <div>
        <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <i data-lucide="sliders-horizontal" class="w-5 h-5 text-indigo-500"></i> Set Per-Model Token Quota
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400">Configure token budgets, request limits, or disable any of the {{ ai_model_count }} AI models.</p>
      </div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div class="sm:col-span-2">
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">AI Model</label>
        <select id="quota-model-key" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
          <option value="*">* — Global Default (All {{ ai_model_count }} AI Models)</option>
          {% for m in ai_models %}
          <option value="{{ m.key }}">{{ m.name }} ({{ m.key }})</option>
          {% endfor %}
        </select>
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Token Limit (0 = unlimited)</label>
        <input id="quota-token-limit" type="number" value="250000" min="0" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Request Limit (0 = unlimited)</label>
        <input id="quota-req-limit" type="number" value="2000" min="0" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1">Cost / 1K Tokens (USD)</label>
        <input id="quota-cost" type="number" step="0.001" value="0.002" min="0" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div class="flex items-end pb-1">
        <label class="inline-flex items-center gap-2.5 cursor-pointer text-sm text-slate-700 dark:text-slate-200">
          <input id="quota-enabled" type="checkbox" checked class="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
          <span>Model Enabled</span>
        </label>
      </div>
    </div>
    <div class="flex flex-col sm:flex-row gap-2">
      <button type="button" onclick="tblincSaveQuota()" class="flex-1 min-h-[44px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow transition">
        <i data-lucide="save" class="w-4 h-4"></i> Save Quota Policy
      </button>
      <button type="button" onclick="tblincResetAllQuotas()" class="min-h-[44px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-sm font-medium hover:bg-slate-100 dark:hover:bg-slate-800 transition">
        <i data-lucide="rotate-ccw" class="w-4 h-4"></i> Reset Counters
      </button>
    </div>
    <p id="quota-status" class="text-xs text-slate-500 dark:text-slate-400"></p>
  </section>
</div>

<!-- Full-Width Issued & Stored AI Keys Table -->
<section data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i> Managed AI Keys
    </h2>
    <a href="{{ admin_prefix }}/aikey/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Manage ORM Table &rarr;</a>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[760px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Name</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Owner</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Provider</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Key (Masked)</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Models</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Tokens Used / Quota</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Status</th>
          <th class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for k in api_keys %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <td class="px-4 sm:px-6 py-3.5 font-semibold text-slate-900 dark:text-white">{{ k.name }}</td>
          <td class="px-4 sm:px-6 py-3.5 text-xs font-mono text-slate-600 dark:text-slate-300">{{ k.owner_username|default:"admin" }}</td>
          <td class="px-4 sm:px-6 py-3.5 uppercase text-xs font-mono text-indigo-600 dark:text-indigo-400">{{ k.provider }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-slate-600 dark:text-slate-300">{{ k.masked_key }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-slate-500">{{ k.allowed_models }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs">{{ k.tokens_used }} / {{ k.token_quota }} ({{ k.requests_used }} reqs)</td>
          <td class="px-4 sm:px-6 py-3.5">
            {% if k.is_active %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">Active</span>
            {% else %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300">Revoked</span>
            {% endif %}
          </td>
          <td class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap space-x-1.5">
            <button type="button" onclick="tblincToggleKey({{ k.id }})" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-medium hover:bg-indigo-100 dark:hover:bg-indigo-600/30">Toggle</button>
            <button type="button" onclick="tblincResetKey({{ k.id }})" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-medium hover:bg-amber-100 dark:hover:bg-amber-600/30">Reset</button>
            <button type="button" onclick="tblincDeleteKey({{ k.id }})" class="px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300 text-xs font-medium hover:bg-rose-100">Delete</button>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="8" class="px-6 py-8 text-center text-xs text-slate-500">No AI keys yet. Generate your first <code>tbl_sk_...</code> key or add a provider key above.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<!-- Full-Width All 25 Models Token Quotas Table -->
<section data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="gauge" class="w-4 h-4 text-indigo-500"></i> All {{ ai_model_count }} AI Models Token Quotas
    </h2>
    <a href="{{ admin_prefix }}/modelquota/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Manage ORM Table &rarr;</a>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[760px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">AI Model</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Category</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Tokens Used / Limit</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Requests</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Est. Cost</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Status</th>
          <th class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap">Action</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for q in model_quotas %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <td class="px-4 sm:px-6 py-3 font-semibold text-slate-900 dark:text-white">
            {{ q.name }} <code class="ml-1 text-[11px] font-normal text-indigo-600 dark:text-indigo-400">({{ q.model_key }})</code>
          </td>
          <td class="px-4 sm:px-6 py-3 text-xs text-slate-500">{{ q.category }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs">
            <div>{{ q.tokens_used }} / {{ q.token_limit }}</div>
            <div class="mt-1 h-1.5 w-32 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
              <div class="h-full bg-indigo-500" style="width: {{ q.token_pct }}%"></div>
            </div>
          </td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs text-slate-600 dark:text-slate-300">{{ q.requests_used }} / {{ q.request_limit }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs text-emerald-600 dark:text-emerald-400">${{ q.cost_usd }}</td>
          <td class="px-4 sm:px-6 py-3">
            {% if q.is_enabled %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">Enabled</span>
            {% else %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300">Disabled</span>
            {% endif %}
          </td>
          <td class="px-4 sm:px-6 py-3 text-right whitespace-nowrap">
            <button type="button" onclick="tblincEditQuotaRow('{{ q.model_key }}', {{ q.token_limit }}, {{ q.request_limit }}, {% if q.is_enabled %}true{% else %}false{% endif %})" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-indigo-100 dark:hover:bg-indigo-600/30 text-indigo-700 dark:text-indigo-300 text-xs font-medium">Configure</button>
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<!-- Full-Width Recent Token Usage Ledger -->
<section data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="list-checks" class="w-4 h-4 text-cyan-500"></i> Live Token Usage Ledger
    </h2>
    <a href="{{ admin_prefix }}/tokenusagelog/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Manage ORM Table &rarr;</a>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[680px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">AI Model</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Key / Caller</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Prompt</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Completion</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Total Tokens</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Latency</th>
          <th class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap">Status</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for u in usage_logs %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <td class="px-4 sm:px-6 py-3"><code class="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 text-xs">{{ u.model_key }}</code></td>
          <td class="px-4 sm:px-6 py-3 text-slate-700 dark:text-slate-200">{{ u.key_name }} <span class="text-slate-400">({{ u.username }})</span></td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs">{{ u.prompt_tokens }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs">{{ u.completion_tokens }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs font-semibold text-indigo-600 dark:text-indigo-400">{{ u.total_tokens }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs text-slate-500">{{ u.latency_ms }} ms</td>
          <td class="px-4 sm:px-6 py-3 text-right font-mono text-xs">{{ u.status }}</td>
        </tr>
        {% empty %}
        <tr><td colspan="7" class="px-6 py-8 text-center text-xs text-slate-500">No metered requests yet. Run any AI model in tblinc AI or Model Hub to see live token usage here.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>
{% endblock %}
{% block scripts %}
<script>
window.tblincCreateAIKey = async function () {
  const resp = await fetch("/api/ai/keys", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: document.getElementById("key-name").value,
      provider: document.getElementById("key-provider").value,
      api_key: document.getElementById("key-secret").value,
      allowed_models: document.getElementById("key-models").value,
      token_quota: parseInt(document.getElementById("key-token-quota").value || "0", 10),
      request_quota: parseInt(document.getElementById("key-req-quota").value || "0", 10)
    })
  });
  const data = await resp.json();
  if (resp.ok && data.key) {
    document.getElementById("key-created-val").textContent = data.key.api_key || data.key.masked_key;
    document.getElementById("key-created-banner").classList.remove("hidden");
    setTimeout(() => window.location.reload(), 2600);
  } else {
    alert(data.error || "Failed to create AI key");
  }
};
window.tblincToggleKey = async function (id) {
  await fetch("/api/ai/keys/" + id + "/toggle", { method: "POST" });
  window.location.reload();
};
window.tblincResetKey = async function (id) {
  await fetch("/api/ai/keys/" + id + "/reset", { method: "POST" });
  window.location.reload();
};
window.tblincDeleteKey = async function (id) {
  await fetch("/api/ai/keys/" + id, { method: "DELETE" });
  window.location.reload();
};
window.tblincEditQuotaRow = function (modelKey, tokenLim, reqLim, enabled) {
  document.getElementById("quota-model-key").value = modelKey;
  document.getElementById("quota-token-limit").value = tokenLim || 250000;
  document.getElementById("quota-req-limit").value = reqLim || 2000;
  document.getElementById("quota-enabled").checked = Boolean(enabled);
  window.scrollTo({ top: 0, behavior: "smooth" });
};
window.tblincSaveQuota = async function () {
  const statusEl = document.getElementById("quota-status");
  statusEl.textContent = "Saving quota policy...";
  const resp = await fetch("/api/ai/quotas", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model_key: document.getElementById("quota-model-key").value,
      token_limit: parseInt(document.getElementById("quota-token-limit").value || "0", 10),
      request_limit: parseInt(document.getElementById("quota-req-limit").value || "0", 10),
      cost_per_1k_tokens: parseFloat(document.getElementById("quota-cost").value || "0.002"),
      is_enabled: document.getElementById("quota-enabled").checked
    })
  });
  if (resp.ok) {
    statusEl.textContent = "Quota policy saved!";
    window.location.reload();
  } else {
    const data = await resp.json();
    statusEl.textContent = "Error: " + (data.error || "Failed");
  }
};
window.tblincResetAllQuotas = async function () {
  await fetch("/api/ai/quotas/reset", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  window.location.reload();
};
</script>
{% endblock %}
"""

ADMIN_SETTINGS = """{% extends "tblinc_admin_base.html" %}
{% block title %}Settings · {{ admin_title }}{% endblock %}
{% block header_title %}Settings{% endblock %}
{% block admin_content %}
<div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
  <!-- Left: General, Theme, AI Engine & Security Configuration -->
  <section data-motion="card" class="lg:col-span-8 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-6 shadow-sm">
    <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
      <div>
        <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <i data-lucide="settings" class="w-5 h-5 text-indigo-500"></i> Platform Settings
        </h2>
        <p class="text-xs text-slate-500 dark:text-slate-400">Saved live in SQLite (<code>tblinc_settings</code>) and applied immediately across your workspace.</p>
      </div>
      <span id="settings-saved-badge" class="hidden px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">Saved</span>
    </div>

    <!-- Branding & Appearance -->
    <div class="space-y-3">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Branding &amp; Appearance</h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Platform Title</label>
          <input id="set-site-title" type="text" value="{{ cfg.site_title }}" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Default Theme</label>
          <select id="set-theme" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
            <option value="system" {% if cfg.default_theme == 'system' %}selected{% endif %}>System Auto</option>
            <option value="light" {% if cfg.default_theme == 'light' %}selected{% endif %}>Light Mode</option>
            <option value="dark" {% if cfg.default_theme == 'dark' %}selected{% endif %}>Dark Mode</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Sidenav Layout</label>
          <select id="set-sidenav" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
            <option value="expanded" {% if cfg.default_sidenav == 'expanded' %}selected{% endif %}>Expanded (Icon + Text)</option>
            <option value="mini" {% if cfg.default_sidenav == 'mini' %}selected{% endif %}>Icon Only (Mini Rail)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- AI Engine & Global Quotas -->
    <div class="space-y-3 pt-4 border-t border-slate-200 dark:border-slate-800">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">AI Engine &amp; Global Quotas</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Default AI Model</label>
          <select id="set-default-model" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
            {% for m in ai_models %}
            <option value="{{ m.key }}" {% if cfg.default_ai_model == m.key %}selected{% endif %}>{{ m.name }} ({{ m.key }})</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Compute Device</label>
          <select id="set-device" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
            <option value="auto" {% if cfg.default_device == 'auto' %}selected{% endif %}>Auto ({{ hardware.preferred_device }})</option>
            <option value="cpu" {% if cfg.default_device == 'cpu' %}selected{% endif %}>CPU ({{ hardware.cpu_cores }} cores)</option>
            <option value="cuda" {% if cfg.default_device == 'cuda' %}selected{% endif %}>NVIDIA CUDA</option>
            <option value="xpu" {% if cfg.default_device == 'xpu' %}selected{% endif %}>Intel XPU</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Global Token Limit (0 = unlimited)</label>
          <input id="set-global-tokens" type="number" min="0" value="{{ cfg.global_token_limit }}" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Global Request Limit (0 = unlimited)</label>
          <input id="set-global-reqs" type="number" min="0" value="{{ cfg.global_request_limit }}" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
        </div>
      </div>
    </div>

    <!-- Security & Access -->
    <div class="space-y-3 pt-4 border-t border-slate-200 dark:border-slate-800">
      <h3 class="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Security &amp; Access</h3>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <label class="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50 cursor-pointer">
          <input id="set-allow-reg" type="checkbox" {% if cfg.allow_registration_bool %}checked{% endif %} class="mt-0.5 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
          <span>
            <span class="block text-sm font-semibold text-slate-900 dark:text-white">Allow User Registration</span>
            <span class="block text-xs text-slate-500">Enable sign-up at <code>/auth/register/</code></span>
          </span>
        </label>
        <label class="flex items-start gap-3 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-950/50 cursor-pointer">
          <input id="set-require-key" type="checkbox" {% if cfg.require_studio_api_key_bool %}checked{% endif %} class="mt-0.5 h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500">
          <span>
            <span class="block text-sm font-semibold text-slate-900 dark:text-white">Require API Key for tblinc AI</span>
            <span class="block text-xs text-slate-500">Enforce <code>X-API-Key</code> on public tblinc AI endpoints</span>
          </span>
        </label>
      </div>
    </div>

    <div class="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
      <p id="settings-msg" class="text-xs text-slate-500 dark:text-slate-400"></p>
      <button type="button" onclick="tblincSaveSettings()" class="w-full sm:w-auto min-h-[44px] inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-lg shadow-indigo-600/25 transition">
        <i data-lucide="save" class="w-4 h-4"></i> Save Settings
      </button>
    </div>
  </section>

  <!-- Right: System & Runtime Diagnostics -->
  <section data-motion="card" class="lg:col-span-4 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
      <i data-lucide="cpu" class="w-5 h-5 text-cyan-500"></i> System Runtime
    </h2>
    <dl class="space-y-3 text-xs sm:text-sm">
      <div class="flex items-center justify-between gap-2">
        <dt class="text-slate-500">AI Models Ready</dt>
        <dd class="font-mono font-semibold text-indigo-600 dark:text-indigo-400">{{ ai_model_count }} models</dd>
      </div>
      <div class="flex items-center justify-between gap-2">
        <dt class="text-slate-500">Preferred Device</dt>
        <dd class="font-mono uppercase font-semibold text-slate-900 dark:text-white">{{ hardware.preferred_device }}</dd>
      </div>
      <div class="flex items-center justify-between gap-2">
        <dt class="text-slate-500">CPU Cores</dt>
        <dd class="font-mono text-slate-700 dark:text-slate-200">{{ hardware.cpu_cores }}</dd>
      </div>
      <div class="flex items-center justify-between gap-2">
        <dt class="text-slate-500">Python Runtime</dt>
        <dd class="font-mono text-slate-700 dark:text-slate-200">{{ hardware.python_version }}</dd>
      </div>
      <div class="flex items-center justify-between gap-2">
        <dt class="text-slate-500">ORM Tables</dt>
        <dd class="font-mono text-slate-700 dark:text-slate-200">{{ total_models }} tables ({{ total_records }} rows)</dd>
      </div>
      <div class="pt-2 border-t border-slate-200 dark:border-slate-800">
        <dt class="text-slate-500 mb-1">SQLite Database</dt>
        <dd class="font-mono text-[11px] break-all rounded-lg bg-slate-100 dark:bg-slate-950 px-2.5 py-2 text-slate-700 dark:text-slate-300">{{ db_path }}</dd>
      </div>
    </dl>
    <div class="pt-2 space-y-2">
      <a href="{{ admin_prefix }}/keys/" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
        <i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i> Open Keys &amp; Quotas
      </a>
      <a href="/api/system/" target="_blank" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
        <i data-lucide="braces" class="w-4 h-4 text-indigo-500"></i> Inspect /api/system/ JSON
      </a>
    </div>
  </section>
</div>
{% endblock %}
{% block scripts %}
<script>
window.tblincSaveSettings = async function () {
  const msg = document.getElementById("settings-msg");
  const badge = document.getElementById("settings-saved-badge");
  msg.textContent = "Saving settings...";
  const themeChoice = document.getElementById("set-theme").value;
  const navChoice = document.getElementById("set-sidenav").value;
  const resp = await fetch("/api/admin/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      site_title: document.getElementById("set-site-title").value,
      default_theme: themeChoice,
      default_sidenav: navChoice,
      default_ai_model: document.getElementById("set-default-model").value,
      default_device: document.getElementById("set-device").value,
      global_token_limit: parseInt(document.getElementById("set-global-tokens").value || "0", 10),
      global_request_limit: parseInt(document.getElementById("set-global-reqs").value || "0", 10),
      allow_registration: document.getElementById("set-allow-reg").checked,
      require_studio_api_key: document.getElementById("set-require-key").checked
    })
  });
  const data = await resp.json();
  if (resp.ok) {
    if (themeChoice === "dark" || themeChoice === "light") {
      localStorage.setItem("tblinc-theme", themeChoice);
      document.documentElement.classList.toggle("dark", themeChoice === "dark");
      if (window.tblincSyncThemeUI) window.tblincSyncThemeUI();
    }
    if (window.tblincApplyAdminSidenav) {
      window.tblincApplyAdminSidenav(navChoice);
    }
    msg.textContent = "Settings saved to SQLite.";
    if (badge) badge.classList.remove("hidden");
    setTimeout(() => window.location.reload(), 900);
  } else {
    msg.textContent = "Error: " + (data.error || "Failed to save settings");
  }
};
</script>
{% endblock %}
"""

ERROR_TEMPLATE = """{% extends "tblinc_base.html" %}
{% block title %}{{ status }} {{ title }}{% endblock %}
{% block body %}
<div class="min-h-screen flex items-center justify-center p-4 sm:p-6">
  <div data-motion="hero" class="max-w-md w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl sm:rounded-3xl p-6 sm:p-8 text-center space-y-4 shadow-xl">
    <div class="inline-flex h-14 w-14 rounded-2xl bg-rose-100 dark:bg-rose-500/15 text-rose-600 dark:text-rose-400 items-center justify-center">
      <i data-lucide="shield-alert" class="w-7 h-7"></i>
    </div>
    <div class="text-4xl font-extrabold text-slate-900 dark:text-white">{{ status }}</div>
    <div class="text-sm text-slate-600 dark:text-slate-300">{{ message }}</div>
    <a href="/" class="inline-flex items-center justify-center gap-2 px-4 py-2.5 min-h-[44px] rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition">
      <i data-lucide="home" class="w-4 h-4"></i> Return Home
    </a>
  </div>
</div>
{% endblock %}
"""


def register_builtin_templates(engine: TemplateEngine) -> None:
    """Install all built-in Light/Dark & PC/Tablet/Mobile responsive templates into a TemplateEngine."""
    from .user_pages import SITE_SHELL_LAYOUT, USER_BILLING_TEMPLATE, USER_PROFILE_TEMPLATE, USER_SETTINGS_TEMPLATE

    engine.register_template("tblinc_base.html", BASE_LAYOUT)
    engine.register_template("tblinc_site_base.html", SITE_SHELL_LAYOUT)
    engine.register_template("tblinc_profile.html", USER_PROFILE_TEMPLATE)
    engine.register_template("tblinc_billing.html", USER_BILLING_TEMPLATE)
    engine.register_template("tblinc_settings.html", USER_SETTINGS_TEMPLATE)
    engine.register_template("tblinc_auth.html", AUTH_TEMPLATE)
    engine.register_template("tblinc_admin_base.html", ADMIN_LAYOUT)
    engine.register_template("tblinc_admin_dashboard.html", ADMIN_DASHBOARD)
    engine.register_template("tblinc_admin_list.html", ADMIN_LIST)
    engine.register_template("tblinc_admin_form.html", ADMIN_FORM)
    engine.register_template("tblinc_admin_delete.html", ADMIN_DELETE)
    engine.register_template("tblinc_ai_studio_panel.html", AI_STUDIO_PANEL)
    engine.register_template("tblinc_ai_studio_js.html", AI_STUDIO_JS)
    engine.register_template("tblinc_admin_ai.html", ADMIN_AI_STUDIO)
    engine.register_template("tblinc_admin_models.html", ADMIN_MODEL_HUB)
    engine.register_template("tblinc_admin_catalog.html", ADMIN_MODEL_HUB)
    engine.register_template("tblinc_admin_train.html", ADMIN_TRAIN)
    engine.register_template("tblinc_admin_keys.html", ADMIN_KEYS_QUOTAS)
    engine.register_template("tblinc_admin_settings.html", ADMIN_SETTINGS)
    engine.register_template("tblinc_error.html", ERROR_TEMPLATE)
