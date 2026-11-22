"""Responsive Light & Dark HTML templates (layouts, components, pages) for generated tblinc apps."""

from __future__ import annotations


def build_html_templates() -> dict[str, str]:
    """Return structured layouts/, components/, and pages/ templates."""
    return {
        "templates/layouts/base.html": '''<!DOCTYPE html>
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
      document.documentElement.classList.toggle("dark", saved ? saved === "dark" : prefersDark);
    })();
  </script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/motion@latest/dist/motion.js"></script>
  <link rel="stylesheet" href="/static/css/theme.css?v=5">
  <style>
    html, body { font-size: 14px; height: 100%; width: 100%; margin: 0; padding: 0; overflow: hidden !important; }
    .tblinc-sidenav { width: 16rem; transition: width 0.2s ease; }
    .tblinc-sidenav[data-sidenav-mode="mini"] { width: 4.5rem !important; }
    .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-label] { display: none !important; }
    .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-item],
    .tblinc-sidenav[data-sidenav-mode="mini"] [data-sidenav-brand] { justify-content: center !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
  </style>
</head>
<body class="fixed inset-0 h-screen w-screen flex bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 text-sm antialiased transition-colors duration-200 overflow-hidden">
  {% include "components/sidenav.html" %}
  <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
    {% include "components/navbar.html" %}
    <div id="site-main-scroll" class="flex-1 overflow-y-auto overflow-x-hidden flex flex-col">
      <main class="flex-1 w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6 sm:space-y-8">
        {% block content %}{% endblock %}
      </main>
      {% include "components/footer.html" %}
    </div>
  </div>
  {% include "components/mobile_nav.html" %}
  <script>
    (function () {
      const ACTIVE_CLS = ["bg-indigo-50", "dark:bg-indigo-500/15", "text-indigo-700", "dark:text-indigo-300", "font-semibold"];
      const INACTIVE_CLS = ["text-slate-700", "dark:text-slate-200", "hover:bg-slate-100", "dark:hover:bg-slate-800/80"];

      function lockViewportTop() {
        if (window.scrollY !== 0 || window.scrollX !== 0) {
          window.scrollTo(0, 0);
        }
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
      }
      window.addEventListener("scroll", lockViewportTop, { passive: true });
      window.addEventListener("hashchange", () => {
        lockViewportTop();
        if (window.location.hash) {
          history.replaceState(null, "", window.location.pathname + window.location.search);
        }
      });

      function applySiteNav(mode) {
        const nav = document.getElementById("site-desktop-sidenav");
        if (!nav) return;
        const valid = mode === "mini" ? "mini" : "expanded";
        nav.setAttribute("data-sidenav-mode", valid);
        localStorage.setItem("tblinc-site-sidenav", valid);
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
      window.tblincApplySiteSidenav = applySiteNav;
      window.tblincToggleSiteSidenavMini = function () {
        const nav = document.getElementById("site-desktop-sidenav");
        if (!nav) return;
        const cur = nav.getAttribute("data-sidenav-mode") || "expanded";
        applySiteNav(cur === "mini" ? "expanded" : "mini");
      };
      window.tblincToggleMobileMenu = function (forceOpen) {
        const drawer = document.getElementById("mobile-nav-drawer");
        const backdrop = document.getElementById("mobile-nav-backdrop");
        if (!drawer || !backdrop) return;
        const shouldOpen = typeof forceOpen === "boolean" ? forceOpen : drawer.classList.contains("hidden");
        drawer.classList.toggle("hidden", !shouldOpen);
        backdrop.classList.toggle("hidden", !shouldOpen);
      };
      window.tblincToggleSidenav = function () {
        if (window.innerWidth >= 1024) {
          window.tblincToggleSiteSidenavMini();
        } else {
          window.tblincToggleMobileMenu();
        }
      };
      window.tblincHighlightSidenavTab = function (tabName) {
        document.querySelectorAll("[data-sidenav-tab]").forEach((el) => {
          const isMatch = el.getAttribute("data-sidenav-tab") === tabName;
          ACTIVE_CLS.forEach((c) => el.classList.toggle(c, isMatch));
          INACTIVE_CLS.forEach((c) => el.classList.toggle(c, !isMatch));
        });
      };
      window.tblincScrollToStudio = function () {
        const scroller = document.getElementById("site-main-scroll");
        const studio = document.getElementById("tblinc-ai-studio");
        if (scroller && studio) {
          scroller.scrollTo({ top: Math.max(0, studio.offsetTop - 16), behavior: "smooth" });
        }
      };
      window.tblincNavStudio = function (ev, tabName) {
        const studio = document.getElementById("tblinc-ai-studio");
        if (!studio) {
          try { sessionStorage.setItem("tblinc-pending-tab", tabName); } catch (e) {}
          return true;
        }
        if (ev) ev.preventDefault();
        lockViewportTop();
        if (window.location.hash || window.location.search) {
          history.replaceState(null, "", "/");
        }
        window.tblincToggleMobileMenu(false);
        if (tabName === "home") {
          window.tblincHighlightSidenavTab("home");
          const scroller = document.getElementById("site-main-scroll");
          if (scroller) scroller.scrollTo({ top: 0, behavior: "smooth" });
        } else {
          if (window.tblincStudioTab) window.tblincStudioTab(tabName);
          window.tblincHighlightSidenavTab(tabName);
        }
        return false;
      };
      applySiteNav(localStorage.getItem("tblinc-site-sidenav") || "expanded");
      window.addEventListener("DOMContentLoaded", () => {
        lockViewportTop();
        if (window.location.hash) {
          history.replaceState(null, "", "/");
        }
        let tab = "";
        try {
          tab = sessionStorage.getItem("tblinc-pending-tab") || "";
          if (tab) sessionStorage.removeItem("tblinc-pending-tab");
        } catch (e) {}
        if (!tab) {
          const params = new URLSearchParams(window.location.search);
          tab = params.get("tab") || "";
        }
        if (tab && ["chat", "images", "video", "audio", "music"].includes(tab)) {
          if (window.tblincStudioTab) window.tblincStudioTab(tab);
          window.tblincHighlightSidenavTab(tab);
          if (window.location.search) history.replaceState(null, "", "/");
        }
      });
    })();
  </script>
  <script src="/static/js/app.js?v=5"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
''',
        "templates/components/sidenav.html": '''<!-- Desktop Full-Height Collapsible Sidenav (Expanded · Icon-Only) -->
<aside id="site-desktop-sidenav" data-sidenav-mode="expanded" class="tblinc-sidenav hidden lg:flex flex-col shrink-0 border-r border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-900/60 backdrop-blur-xl h-full">
  <div data-sidenav-brand class="h-16 px-4 border-b border-slate-200 dark:border-slate-800/80 flex items-center gap-3 shrink-0">
    <a href="/" title="{{ site_title }}" class="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
      <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
    </a>
    <div data-sidenav-label class="min-w-0">
      <a href="/" class="font-bold text-sm text-slate-900 dark:text-white leading-tight tracking-tight truncate block">{{ site_title }}</a>
    </div>
  </div>
  <div class="flex-1 p-3 space-y-1 overflow-y-auto no-scrollbar">
    <div data-sidenav-label class="px-3 pt-1 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Workspace</div>
    <a href="/" onclick="return tblincNavStudio(event, 'home')" data-sidenav-tab="home" title="Overview" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition {% if active_nav == 'home' %}bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-semibold{% else %}text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80{% endif %}">
      <i data-lucide="home" class="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0"></i>
      <span data-sidenav-label class="truncate">Overview</span>
    </a>
    <a href="/" onclick="return tblincNavStudio(event, 'chat')" data-sidenav-tab="chat" title="AI Chat" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
      <i data-lucide="message-square" class="w-4 h-4 text-indigo-500 shrink-0"></i>
      <span data-sidenav-label class="truncate">AI Chat</span>
    </a>
    <a href="/" onclick="return tblincNavStudio(event, 'images')" data-sidenav-tab="images" title="AI Images" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
      <i data-lucide="image" class="w-4 h-4 text-pink-500 shrink-0"></i>
      <span data-sidenav-label class="truncate">AI Images</span>
    </a>
    <a href="/" onclick="return tblincNavStudio(event, 'video')" data-sidenav-tab="video" title="AI Video" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
      <i data-lucide="film" class="w-4 h-4 text-cyan-500 shrink-0"></i>
      <span data-sidenav-label class="truncate">AI Video</span>
    </a>
    <a href="/" onclick="return tblincNavStudio(event, 'audio')" data-sidenav-tab="audio" title="AI Audio" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
      <i data-lucide="mic" class="w-4 h-4 text-emerald-500 shrink-0"></i>
      <span data-sidenav-label class="truncate">AI Audio</span>
    </a>
    <a href="/" onclick="return tblincNavStudio(event, 'music')" data-sidenav-tab="music" title="AI Music" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
      <i data-lucide="music" class="w-4 h-4 text-amber-500 shrink-0"></i>
      <span data-sidenav-label class="truncate">AI Music</span>
    </a>

    <div data-sidenav-label class="px-3 pt-4 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Account</div>
    <a href="/profile/" title="Profile & AI Keys" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition {% if active_nav == 'profile' %}bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-semibold{% else %}text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80{% endif %}">
      <i data-lucide="key-round" class="w-4 h-4 text-emerald-500 shrink-0"></i>
      <span data-sidenav-label class="truncate">Profile &amp; AI Key</span>
    </a>
    <a href="/billing/" title="Billing & Balance" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition {% if active_nav == 'billing' %}bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-semibold{% else %}text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80{% endif %}">
      <i data-lucide="credit-card" class="w-4 h-4 text-cyan-500 shrink-0"></i>
      <span data-sidenav-label class="truncate">Billing</span>
    </a>
    <a href="/settings/" title="Settings" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition {% if active_nav == 'settings' %}bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-semibold{% else %}text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80{% endif %}">
      <i data-lucide="settings" class="w-4 h-4 text-slate-500 dark:text-slate-400 shrink-0"></i>
      <span data-sidenav-label class="truncate">Settings</span>
    </a>
  </div>
</aside>
''',
        "templates/components/navbar.html": '''<nav class="shrink-0 z-30 h-16 border-b border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-950/90 backdrop-blur-xl transition-colors">
  <div class="w-full px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between gap-3">
    <div class="flex items-center gap-2 min-w-0">
      <button type="button" onclick="tblincToggleSidenav()" title="Toggle Sidenav" aria-label="Toggle sidenav" class="inline-flex items-center justify-center p-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:border-indigo-400 transition shrink-0">
        <i data-lucide="chevrons-left" data-site-nav-icon-collapse class="w-4 h-4"></i>
        <i data-lucide="chevrons-right" data-site-nav-icon-expand class="w-4 h-4 hidden"></i>
      </button>
    </div>

    <div class="flex items-center gap-2 text-sm shrink-0">
      <button type="button" data-theme-btn onclick="tblincToggleTheme()" aria-label="Toggle Light/Dark theme" class="inline-flex items-center gap-1.5 px-2.5 sm:px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-100/80 dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:border-indigo-400 transition">
        <i data-lucide="sun" data-theme-sun class="w-4 h-4 text-amber-500 hidden"></i>
        <i data-lucide="moon" data-theme-moon class="w-4 h-4 text-indigo-600"></i>
        <span data-theme-label class="hidden sm:inline text-xs font-medium">Dark</span>
      </button>
      {% if user %}
      <a href="/profile/" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-50 dark:bg-indigo-500/15 border border-indigo-200 dark:border-indigo-500/30 text-indigo-700 dark:text-indigo-300 font-semibold hover:bg-indigo-100 dark:hover:bg-indigo-500/25 transition">
        <i data-lucide="user-circle" class="w-4 h-4"></i>
        <span class="max-w-[120px] truncate">{{ user.username }}</span>
      </a>
      <a href="/auth/logout/" title="Sign Out" class="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
        <i data-lucide="log-out" class="w-4 h-4"></i><span>Sign Out</span>
      </a>
      {% else %}
      <a href="/auth/login/" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 font-medium transition">
        <i data-lucide="log-in" class="w-4 h-4"></i><span>Sign In</span>
      </a>
      <a href="/auth/register/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-sm shadow-indigo-600/25 transition">
        <i data-lucide="user-plus" class="w-4 h-4"></i><span>Sign Up</span>
      </a>
      {% endif %}
    </div>
  </div>
</nav>

<!-- Mobile & Tablet Left Slide-Over Sidenav Drawer -->
<div id="mobile-nav-backdrop" onclick="tblincToggleMobileMenu(false)" class="hidden fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"></div>
<aside id="mobile-nav-drawer" class="hidden fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] flex flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl lg:hidden">
  <div class="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <span class="font-bold text-slate-900 dark:text-white">{{ site_title }} Menu</span>
    <button type="button" onclick="tblincToggleMobileMenu(false)" aria-label="Close menu" class="p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800">
      <i data-lucide="x" class="w-5 h-5"></i>
    </button>
  </div>
  <div class="flex-1 p-4 space-y-1.5 overflow-y-auto text-sm">
    <div class="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Workspace</div>
    <a href="/" onclick="return tblincNavStudio(event, 'home')" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="home" class="w-4 h-4 text-indigo-500"></i> Overview</a>
    <a href="/" onclick="return tblincNavStudio(event, 'chat')" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="message-square" class="w-4 h-4 text-indigo-500"></i> AI Chat</a>
    <a href="/" onclick="return tblincNavStudio(event, 'images')" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="image" class="w-4 h-4 text-pink-500"></i> AI Images</a>
    <a href="/" onclick="return tblincNavStudio(event, 'video')" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="film" class="w-4 h-4 text-cyan-500"></i> AI Video</a>
    <a href="/" onclick="return tblincNavStudio(event, 'audio')" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="mic" class="w-4 h-4 text-emerald-500"></i> AI Audio</a>
    <a href="/" onclick="return tblincNavStudio(event, 'music')" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="music" class="w-4 h-4 text-amber-500"></i> AI Music</a>
    <div class="pt-3 px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Account</div>
    <a href="/profile/" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i> Profile &amp; AI Key</a>
    <a href="/billing/" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="credit-card" class="w-4 h-4 text-cyan-500"></i> Billing</a>
    <a href="/settings/" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="settings" class="w-4 h-4 text-slate-500"></i> Settings</a>
    {% if user %}
    <a href="/auth/logout/" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-500/10 mt-2"><i data-lucide="log-out" class="w-4 h-4"></i> Sign Out ({{ user.username }})</a>
    {% else %}
    <a href="/auth/login/" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 mt-2"><i data-lucide="log-in" class="w-4 h-4"></i> Sign In</a>
    <a href="/auth/register/" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold mt-1"><i data-lucide="user-plus" class="w-4 h-4"></i> Sign Up</a>
    {% endif %}
  </div>
</aside>
''',
        "templates/components/mobile_nav.html": '''<!-- Sticky Mobile Bottom Tab Bar (< md) -->
<nav aria-label="Mobile quick navigation" class="md:hidden fixed bottom-0 inset-x-0 z-30 border-t border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-950/95 backdrop-blur-xl">
  <div class="grid grid-cols-4 text-[11px] font-medium">
    <a href="/" onclick="return tblincNavStudio(event, 'home')" class="flex flex-col items-center justify-center py-2.5 gap-1 {% if active_nav == 'home' %}text-indigo-600 dark:text-indigo-400 font-semibold{% else %}text-slate-600 dark:text-slate-300{% endif %}">
      <i data-lucide="home" class="w-4 h-4"></i><span>Home</span>
    </a>
    <a href="/" onclick="return tblincNavStudio(event, 'chat')" class="flex flex-col items-center justify-center py-2.5 gap-1 text-slate-600 dark:text-slate-300">
      <i data-lucide="message-square" class="w-4 h-4"></i><span>Chat</span>
    </a>
    <a href="/profile/" class="flex flex-col items-center justify-center py-2.5 gap-1 {% if active_nav == 'profile' %}text-indigo-600 dark:text-indigo-400 font-semibold{% else %}text-slate-600 dark:text-slate-300{% endif %}">
      <i data-lucide="key-round" class="w-4 h-4"></i><span>AI Key</span>
    </a>
    <a href="/billing/" class="flex flex-col items-center justify-center py-2.5 gap-1 {% if active_nav == 'billing' %}text-indigo-600 dark:text-indigo-400 font-semibold{% else %}text-slate-600 dark:text-slate-300{% endif %}">
      <i data-lucide="credit-card" class="w-4 h-4"></i><span>Billing</span>
    </a>
  </div>
</nav>
''',
        "templates/components/footer.html": '''<footer class="border-t border-slate-200 dark:border-slate-800/80 mt-12 sm:mt-16 py-8 pb-24 md:pb-8 text-xs text-slate-500 dark:text-slate-400">
  <div class="w-full px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
    <div class="flex items-center gap-2 text-center sm:text-left">
      <i data-lucide="sparkles" class="w-4 h-4 text-indigo-500 shrink-0"></i>
      <span><strong>{{ site_title }}</strong> · PC · Tablet · Mobile · Light &amp; Dark</span>
    </div>
    <div class="flex flex-wrap items-center justify-center gap-4">
      <a href="/profile/" class="hover:text-slate-900 dark:hover:text-white transition">Profile &amp; AI Key</a>
      <a href="/billing/" class="hover:text-slate-900 dark:hover:text-white transition">Billing</a>
      <a href="/settings/" class="hover:text-slate-900 dark:hover:text-white transition">Settings</a>
      <a href="/api/system/" class="hover:text-slate-900 dark:hover:text-white transition">System API</a>
    </div>
  </div>
</footer>
''',
        "templates/pages/home.html": '''{% extends "layouts/base.html" %}
{% block content %}
<section data-motion="hero" class="hero-backdrop relative overflow-hidden rounded-2xl sm:rounded-3xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/90 p-6 sm:p-8 lg:p-10 shadow-xl shadow-slate-200/60 dark:shadow-indigo-950/30">
  <div class="max-w-3xl space-y-4">
    <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] sm:text-xs font-semibold bg-indigo-50 dark:bg-cyan-500/15 text-indigo-700 dark:text-cyan-300 border border-indigo-200 dark:border-cyan-500/30">
      <i data-lucide="sparkles" class="w-3.5 h-3.5 shrink-0"></i> Chat · Images · Video · Audio · Music · Personal AI Keys
    </span>
    <h1 class="text-2xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white">
      {% if site_title == 'tblinc AI' %}tblinc <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">AI</span>{% else %}{{ site_title }} <span class="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-cyan-500 dark:from-indigo-400 dark:to-cyan-400">· tblinc AI</span>{% endif %}
    </h1>
    <p class="text-slate-600 dark:text-slate-300 text-sm sm:text-base leading-relaxed">
      Create, chat, and build in one place — generate instant <strong>AI Chat</strong> answers, <strong>Images</strong>, <strong>Video</strong>, natural <strong>Voice Audio</strong>, and <strong>Music</strong> with your personal AI API key and live wallet balance.
    </p>
    <div class="flex flex-col sm:flex-row flex-wrap gap-2.5 pt-1">
      <button type="button" onclick="tblincScrollToStudio()" class="w-full sm:w-auto min-h-[42px] inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition">
        <i data-lucide="sparkles" class="w-4 h-4"></i> Start Creating
      </button>
      {% if user %}
      <a href="/profile/" class="w-full sm:w-auto min-h-[42px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold text-sm border border-slate-200 dark:border-slate-700 transition">
        <i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i> Profile &amp; AI Keys ({{ user.username }})
      </a>
      <a href="/billing/" class="w-full sm:w-auto min-h-[42px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold text-sm border border-slate-200 dark:border-slate-700 transition">
        <i data-lucide="credit-card" class="w-4 h-4 text-cyan-500"></i> Billing &amp; Balance
      </a>
      {% else %}
      <a href="/auth/register/" class="w-full sm:w-auto min-h-[42px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm shadow-sm transition">
        <i data-lucide="user-plus" class="w-4 h-4"></i> Sign Up Free ($10 Credit)
      </a>
      <a href="/auth/login/" class="w-full sm:w-auto min-h-[42px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200 font-semibold text-sm border border-slate-200 dark:border-slate-700 transition">
        <i data-lucide="log-in" class="w-4 h-4 text-indigo-500"></i> Sign In
      </a>
      {% endif %}
    </div>
  </div>
</section>

{% include "tblinc_ai_studio_panel.html" %}
{% endblock %}
{% block scripts %}
{% include "tblinc_ai_studio_js.html" %}
{% endblock %}
''',
        "templates/pages/models.html": '''{% extends "layouts/base.html" %}
{% block title %}AI Model Hub · {{ site_title }}{% endblock %}
{% block content %}
<div data-motion="hero" class="space-y-4">
  <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
    <div>
      <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 mb-2 rounded-full text-[11px] font-semibold bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">
        <i data-lucide="shield-check" class="w-3.5 h-3.5"></i> Admin Authenticated · {{ user.username }}
      </span>
      <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">AI Model Hub ({{ ai_count }})</h1>
      <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">Admin-protected hub to search, filter, and run live inference across all {{ ai_count }} built-in AI models.</p>
    </div>
    <div class="relative w-full md:w-72">
      <i data-lucide="search" class="w-4 h-4 text-slate-400 absolute left-3.5 top-3"></i>
      <input type="search" oninput="tblincFilterModels(this.value)" placeholder="Filter models..." class="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500">
    </div>
  </div>
  <div class="flex items-center gap-2 overflow-x-auto no-scrollbar pb-1">
    <a href="/models/" class="shrink-0 px-3.5 py-2 rounded-xl text-xs font-semibold border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:border-indigo-400 transition">All</a>
    {% for cat in categories %}
    <a href="/models/?category={{ cat }}" class="shrink-0 px-3.5 py-2 rounded-xl text-xs font-medium border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:border-indigo-400 transition">{{ cat }}</a>
    {% endfor %}
  </div>
</div>

<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
  {% for m in ai_models %}
  <div data-motion="card" data-model-card data-search="{{ m.name }} {{ m.key }} {{ m.category }} {{ m.task }} {{ m.description }}" class="glass-panel border border-slate-200 dark:border-slate-800 hover:border-indigo-400 dark:hover:border-cyan-500/40 rounded-2xl p-4 sm:p-5 flex flex-col justify-between transition shadow-sm">
    <div>
      <div class="flex items-center justify-between gap-2 mb-2">
        <span class="text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30 truncate">{{ m.category }}</span>
        <code class="text-[11px] text-slate-500 dark:text-slate-400 shrink-0">{{ m.key }}</code>
      </div>
      <h3 class="font-bold text-slate-900 dark:text-white">{{ m.name }}</h3>
      <p class="text-xs text-cyan-700 dark:text-cyan-400 mt-0.5">{{ m.task }}</p>
      <p class="text-xs text-slate-600 dark:text-slate-400 mt-1.5">{{ m.description }}</p>
    </div>
    <div class="mt-4 pt-3 border-t border-slate-200 dark:border-slate-800/80 space-y-2">
      <textarea id="cat-inp-{{ m.key }}" rows="2" class="w-full rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 p-2.5 font-mono text-xs text-slate-800 dark:text-slate-200">{{ m.input_json }}</textarea>
      <button onclick="tblincRunModel('{{ m.key }}', 'cat')" class="w-full min-h-[42px] inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-semibold transition">
        <i data-lucide="play" class="w-3.5 h-3.5"></i> Run Live Model
      </button>
      <div id="cat-wrap-{{ m.key }}" class="hidden space-y-1.5">
        <div class="flex items-center justify-between text-[11px] text-slate-500">
          <span id="cat-lat-{{ m.key }}" class="font-mono text-emerald-600 dark:text-emerald-400"></span>
          <button type="button" onclick="tblincCopyOutput('cat-out-{{ m.key }}')" class="hover:text-indigo-500 inline-flex items-center gap-1"><i data-lucide="copy" class="w-3 h-3"></i> Copy</button>
        </div>
        <pre id="cat-out-{{ m.key }}" class="rounded-xl bg-slate-900 dark:bg-slate-950 border border-emerald-500/30 p-2.5 text-[11px] text-emerald-300 overflow-x-auto max-h-44"></pre>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
{% endblock %}
''',
        "templates/pages/experiments.html": '''{% extends "layouts/base.html" %}
{% block title %}Experiments · {{ site_title }}{% endblock %}
{% block content %}
<div data-motion="hero" class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
  <div>
    <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">Experiments &amp; Inference Logs</h1>
    <p class="text-sm text-slate-600 dark:text-slate-400 mt-1">Backed by SQLite ORM models and manageable in the Admin Panel.</p>
  </div>
  <a href="/experiments/new/" class="w-full sm:w-auto min-h-[44px] inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-sm transition">
    <i data-lucide="plus-circle" class="w-4 h-4"></i> New Experiment
  </a>
</div>

<section class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {% for exp in experiments %}
  <div data-motion="card" class="glass-panel border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 space-y-2 shadow-sm">
    <div class="flex items-center justify-between gap-2">
      <span class="text-xs font-mono px-2 py-0.5 rounded-lg bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 truncate">{{ exp.model_key }}</span>
      <span class="text-xs font-mono px-2 py-0.5 rounded-lg bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 shrink-0">{{ exp.accuracy_score }}</span>
    </div>
    <h3 class="font-bold text-slate-900 dark:text-white">{{ exp.name }}</h3>
    <p class="text-xs text-slate-600 dark:text-slate-400">{{ exp.description }}</p>
  </div>
  {% empty %}
  <p class="text-sm text-slate-500">No experiments saved yet.</p>
  {% endfor %}
</section>

<section class="w-full glass-panel border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="table-2" class="w-4 h-4 text-indigo-500"></i> Recent Inference Logs
    </h2>
    <a href="/admin/inferencelog/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Manage in Admin &rarr;</a>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[600px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">ID</th>
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">AI Model</th>
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">Prediction</th>
          <th class="px-4 sm:px-6 py-3.5 font-semibold whitespace-nowrap">Confidence</th>
          <th class="px-4 sm:px-6 py-3.5 text-right font-semibold whitespace-nowrap">Latency</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800">
        {% for log in recent_logs %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition">
          <td class="px-4 sm:px-6 py-3.5 font-mono text-slate-500">#{{ log.id }}</td>
          <td class="px-4 sm:px-6 py-3.5 whitespace-nowrap"><code class="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-semibold text-xs">{{ log.model_key }}</code></td>
          <td class="px-4 sm:px-6 py-3.5 text-slate-700 dark:text-slate-200 max-w-md lg:max-w-xl truncate">{{ log.output_prediction|truncate:120 }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-emerald-600 dark:text-emerald-400">{{ log.confidence }}</td>
          <td class="px-4 sm:px-6 py-3.5 text-right font-mono text-slate-500 whitespace-nowrap">{{ log.latency_ms }} ms</td>
        </tr>
        {% empty %}
        <tr>
          <td colspan="5" class="px-6 py-8 text-center text-xs text-slate-500">Run any AI model from the playground to record live logs here.</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>
{% endblock %}
''',
        "templates/pages/create_experiment.html": '''{% extends "layouts/base.html" %}
{% block title %}New Experiment · {{ site_title }}{% endblock %}
{% block content %}
<div data-motion="hero" class="max-w-xl mx-auto glass-panel border border-slate-200 dark:border-slate-800 rounded-2xl sm:rounded-3xl p-5 sm:p-8 space-y-6 shadow-xl">
  <div class="flex items-center justify-between gap-2">
    <h1 class="text-lg sm:text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="flask-conical" class="w-5 h-5 text-cyan-600 dark:text-cyan-400"></i> Create AI Experiment
    </h1>
    <a href="/experiments/" class="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white shrink-0">&larr; Back</a>
  </div>
  <form method="post" class="space-y-4">
    {% csrf_token %}
    {{ form_html|safe }}
    <button type="submit" class="w-full min-h-[44px] py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition">
      Save Experiment
    </button>
  </form>
</div>
{% endblock %}
''',
    }
