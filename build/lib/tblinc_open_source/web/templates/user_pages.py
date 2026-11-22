"""Built-in User Profile (Personal AI Keys), Workspace Settings, and Unified Site Shell templates."""

from __future__ import annotations

SITE_SHELL_LAYOUT = """{% extends "tblinc_base.html" %}
{% block body %}
<div class="fixed inset-0 h-screen w-screen flex bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 text-sm antialiased transition-colors duration-200 overflow-hidden">
  <!-- Mobile Slide-Over Menu Drawer (Left Side) -->
  <div id="site-drawer-backdrop" onclick="tblincToggleSiteDrawer(false)" class="hidden fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden"></div>
  <aside id="site-mobile-drawer" class="hidden fixed inset-y-0 left-0 z-50 w-72 max-w-[85vw] flex flex-col border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl lg:hidden">
    <div class="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
      <span class="font-bold text-slate-900 dark:text-white">{{ site_title|default:"tblinc AI" }} Menu</span>
      <button type="button" onclick="tblincToggleSiteDrawer(false)" aria-label="Close menu" class="p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800">
        <i data-lucide="x" class="w-5 h-5"></i>
      </button>
    </div>
    <div class="flex-1 p-4 space-y-1.5 overflow-y-auto text-sm">
      <div class="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400">Workspace</div>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','home')}catch(e){}" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="home" class="w-4 h-4 text-indigo-500"></i> Overview</a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','chat')}catch(e){}" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="message-square" class="w-4 h-4 text-indigo-500"></i> AI Chat</a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','images')}catch(e){}" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="image" class="w-4 h-4 text-pink-500"></i> AI Images</a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','video')}catch(e){}" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="film" class="w-4 h-4 text-cyan-500"></i> AI Video</a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','audio')}catch(e){}" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="mic" class="w-4 h-4 text-emerald-500"></i> AI Audio</a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','music')}catch(e){}" class="flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"><i data-lucide="music" class="w-4 h-4 text-amber-500"></i> AI Music</a>
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

  <!-- Desktop Full-Height Sidenav (Top to Bottom) -->
  <aside id="site-desktop-sidenav" data-sidenav-mode="expanded" class="tblinc-sidenav hidden lg:flex flex-col shrink-0 border-r border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-900/60 backdrop-blur-xl h-full">
    <div data-sidenav-brand class="h-16 px-4 border-b border-slate-200 dark:border-slate-800/80 flex items-center gap-3 shrink-0">
      <a href="/" title="{{ site_title|default:'tblinc AI' }}" class="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 shrink-0">
        <i data-lucide="cpu" class="w-4 h-4 text-white"></i>
      </a>
      <div data-sidenav-label class="min-w-0">
        <a href="/" class="font-bold text-sm text-slate-900 dark:text-white leading-tight tracking-tight truncate block">{{ site_title|default:"tblinc AI" }}</a>
      </div>
    </div>
    <div class="flex-1 p-3 space-y-1 overflow-y-auto no-scrollbar">
      <div data-sidenav-label class="px-3 pt-1 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Workspace</div>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','home')}catch(e){}" title="Overview" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="home" class="w-4 h-4 text-indigo-600 dark:text-indigo-400 shrink-0"></i>
        <span data-sidenav-label class="truncate">Overview</span>
      </a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','chat')}catch(e){}" title="AI Chat" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="message-square" class="w-4 h-4 text-indigo-500 shrink-0"></i>
        <span data-sidenav-label class="truncate">AI Chat</span>
      </a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','images')}catch(e){}" title="AI Images" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="image" class="w-4 h-4 text-pink-500 shrink-0"></i>
        <span data-sidenav-label class="truncate">AI Images</span>
      </a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','video')}catch(e){}" title="AI Video" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="film" class="w-4 h-4 text-cyan-500 shrink-0"></i>
        <span data-sidenav-label class="truncate">AI Video</span>
      </a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','audio')}catch(e){}" title="AI Audio" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="mic" class="w-4 h-4 text-emerald-500 shrink-0"></i>
        <span data-sidenav-label class="truncate">AI Audio</span>
      </a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','music')}catch(e){}" title="AI Music" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80 transition">
        <i data-lucide="music" class="w-4 h-4 text-amber-500 shrink-0"></i>
        <span data-sidenav-label class="truncate">AI Music</span>
      </a>

      <div data-sidenav-label class="px-3 pt-4 pb-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Account</div>
      <a href="/profile/" title="Profile & AI Key" data-sidenav-item class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition {% if active_nav == 'profile' %}bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 font-semibold{% else %}text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/80{% endif %}">
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

  <!-- Right Column: Fixed Navbar + Scrollable Content -->
  <div class="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
    <nav class="shrink-0 z-30 h-16 border-b border-slate-200 dark:border-slate-800/80 bg-white/90 dark:bg-slate-950/90 backdrop-blur-xl transition-colors">
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

    <div class="flex-1 overflow-y-auto overflow-x-hidden">
      <main class="w-full px-4 sm:px-6 lg:px-8 py-6 sm:py-8 pb-24 md:pb-10 space-y-6">
        {% block site_content %}{% endblock %}
      </main>
    </div>
  </div>

  <!-- Mobile Bottom Quick Navigation -->
  <nav aria-label="Mobile quick navigation" class="md:hidden fixed bottom-0 inset-x-0 z-30 border-t border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-950/95 backdrop-blur-xl">
    <div class="grid grid-cols-4 text-[11px] font-medium">
      <a href="/" class="flex flex-col items-center justify-center py-2.5 gap-1 text-slate-600 dark:text-slate-300">
        <i data-lucide="home" class="w-4 h-4"></i><span>Home</span>
      </a>
      <a href="/" onclick="try{sessionStorage.setItem('tblinc-pending-tab','chat')}catch(e){}" class="flex flex-col items-center justify-center py-2.5 gap-1 text-slate-600 dark:text-slate-300">
        <i data-lucide="message-square" class="w-4 h-4"></i><span>Chat</span>
      </a>
      <a href="/profile/" class="flex flex-col items-center justify-center py-2.5 gap-1 {% if active_nav == 'profile' %}text-indigo-600 dark:text-indigo-400 font-semibold{% else %}text-slate-600 dark:text-slate-300{% endif %}">
        <i data-lucide="key-round" class="w-4 h-4"></i><span>AI Key</span>
      </a>
      <a href="/settings/" class="flex flex-col items-center justify-center py-2.5 gap-1 {% if active_nav == 'settings' %}text-indigo-600 dark:text-indigo-400 font-semibold{% else %}text-slate-600 dark:text-slate-300{% endif %}">
        <i data-lucide="settings" class="w-4 h-4"></i><span>Settings</span>
      </a>
    </div>
  </nav>
</div>

<script>
(function () {
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
  window.tblincToggleSiteDrawer = function (forceOpen) {
    const d = document.getElementById("site-mobile-drawer");
    const b = document.getElementById("site-drawer-backdrop");
    if (!d || !b) return;
    const open = typeof forceOpen === "boolean" ? forceOpen : d.classList.contains("hidden");
    d.classList.toggle("hidden", !open);
    b.classList.toggle("hidden", !open);
  };
  window.tblincToggleSidenav = function () {
    if (window.innerWidth >= 1024) {
      window.tblincToggleSiteSidenavMini();
    } else {
      window.tblincToggleSiteDrawer();
    }
  };
  window.tblincSiteToast = function (msg) {
    let el = document.getElementById("tblinc-site-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "tblinc-site-toast";
      el.className = "fixed bottom-20 md:bottom-6 right-4 sm:right-6 z-50 px-4 py-2.5 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-semibold shadow-xl";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.remove("hidden");
    clearTimeout(window.__tblincSiteToastT);
    window.__tblincSiteToastT = setTimeout(() => el.classList.add("hidden"), 2400);
  };
  applySiteNav(localStorage.getItem("tblinc-site-sidenav") || "expanded");
})();
</script>
{% endblock %}
"""

USER_PROFILE_TEMPLATE = """{% extends "tblinc_site_base.html" %}
{% block title %}Profile & AI Keys · {{ site_title|default:"tblinc AI" }}{% endblock %}
{% block site_content %}
{% if welcome %}
<div data-motion="hero" class="rounded-2xl border border-emerald-300 dark:border-emerald-500/40 bg-emerald-50 dark:bg-emerald-500/10 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
  <div class="flex items-start gap-3">
    <span class="h-9 w-9 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0">
      <i data-lucide="sparkles" class="w-4 h-4"></i>
    </span>
    <div>
      <div class="font-bold text-emerald-900 dark:text-emerald-200">Welcome, {{ profile_user.username }}! Your AI workspace is ready.</div>
      <p class="text-xs text-emerald-700 dark:text-emerald-300 mt-0.5">We automatically provisioned a starter personal <code>tbl_sk_...</code> AI key below. Click <strong>Copy</strong> or <strong>Use in Studio</strong> to start calling all AI models.</p>
    </div>
  </div>
  <a href="/" class="shrink-0 inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition">
    <i data-lucide="message-square" class="w-3.5 h-3.5"></i> Open AI Workspace
  </a>
</div>
{% endif %}

{% if flash_msg %}
<div class="rounded-xl border border-emerald-300 dark:border-emerald-500/40 bg-emerald-50 dark:bg-emerald-500/10 px-4 py-3 text-xs font-medium text-emerald-800 dark:text-emerald-200">{{ flash_msg }}</div>
{% endif %}
{% if flash_err %}
<div class="rounded-xl border border-rose-300 dark:border-rose-500/40 bg-rose-50 dark:bg-rose-500/10 px-4 py-3 text-xs font-medium text-rose-800 dark:text-rose-200">{{ flash_err }}</div>
{% endif %}

<!-- Profile Header Card -->
<section data-motion="hero" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
  <div class="flex items-center gap-4 min-w-0">
    <div class="h-14 w-14 rounded-2xl bg-gradient-to-br from-indigo-600 to-cyan-500 text-white font-extrabold text-lg flex items-center justify-center shadow-lg shadow-indigo-500/25 shrink-0">
      {{ user_initials }}
    </div>
    <div class="min-w-0">
      <div class="flex flex-wrap items-center gap-2">
        <h1 class="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white truncate">{{ profile_user.username }}</h1>
        {% if profile_user.is_staff %}
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-500/30">Admin</span>
        {% else %}
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-500/30">Member</span>
        {% endif %}
      </div>
      <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5 truncate">{{ profile_user.email|default:"No email set" }} · Joined {{ profile_user.created_at }}</p>
    </div>
  </div>
  <div class="flex flex-wrap items-center gap-2 shrink-0">
    <a href="/billing/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-500/15 border border-emerald-200 dark:border-emerald-500/30 text-xs font-semibold text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 transition">
      <i data-lucide="credit-card" class="w-4 h-4"></i> Balance: ${{ summary.balance_display|default:"10.00" }}
    </a>
    <a href="/settings/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
      <i data-lucide="settings" class="w-4 h-4"></i> Settings
    </a>
    <a href="/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition">
      <i data-lucide="sparkles" class="w-4 h-4"></i> AI Workspace
    </a>
  </div>
</section>

<!-- Personal Quota & Usage Summary -->
<section class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
  <a href="/billing/" data-motion="card" class="glass border border-slate-200 dark:border-slate-800 hover:border-emerald-400 rounded-2xl p-4 sm:p-5 shadow-sm transition block">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between"><span>Wallet Balance</span><i data-lucide="wallet" class="w-4 h-4 text-emerald-500"></i></div>
    <div class="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">${{ summary.balance_display|default:"10.00" }} <span class="text-xs font-semibold uppercase text-slate-400">{{ summary.plan_tier|default:"STARTER" }}</span></div>
  </a>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between"><span>Active AI Keys</span><i data-lucide="key-round" class="w-4 h-4 text-indigo-500"></i></div>
    <div class="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{{ summary.active_keys }} <span class="text-xs font-normal text-slate-400">/ {{ summary.total_keys }}</span></div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between"><span>Tokens Used / Quota</span><i data-lucide="flame" class="w-4 h-4 text-cyan-500"></i></div>
    <div class="mt-2 text-xl sm:text-2xl font-bold text-slate-900 dark:text-white">{{ summary.tokens_used }} <span class="text-xs font-normal text-slate-400">/ {{ summary.total_quota }}</span></div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between"><span>AI Requests</span><i data-lucide="activity" class="w-4 h-4 text-amber-500"></i></div>
    <div class="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{{ summary.total_requests }}</div>
  </div>
</section>

<!-- Revealed / Newly Generated Key Banner -->
<div id="user-key-reveal-box" class="hidden rounded-2xl border border-emerald-300 dark:border-emerald-500/40 bg-emerald-50 dark:bg-emerald-500/10 p-4 space-y-2">
  <div class="flex items-center justify-between gap-2">
    <span id="user-key-reveal-title" class="text-xs font-bold text-emerald-800 dark:text-emerald-200 flex items-center gap-1.5">
      <i data-lucide="key-round" class="w-4 h-4"></i> Personal AI Key Ready
    </span>
    <button type="button" onclick="document.getElementById('user-key-reveal-box').classList.add('hidden')" class="text-xs text-slate-500 hover:text-slate-800 dark:hover:text-white">Dismiss</button>
  </div>
  <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
    <code id="user-key-reveal-val" class="flex-1 rounded-xl bg-white dark:bg-slate-950 border border-emerald-300 dark:border-emerald-500/30 px-3 py-2 font-mono text-xs text-emerald-700 dark:text-emerald-300 break-all"></code>
    <div class="flex items-center gap-2 shrink-0">
      <button type="button" onclick="tblincCopyRevealedKey()" class="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition">Copy Key</button>
      <button type="button" onclick="tblincActivateRevealedKey()" class="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition">Use in tblinc AI</button>
    </div>
  </div>
</div>

<!-- Create Personal AI Key & Quick API Example -->
<div class="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
  <section data-motion="card" class="lg:col-span-7 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <div class="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-3">
      <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
        <i data-lucide="plus-circle" class="w-5 h-5 text-emerald-500"></i> Generate Personal AI Key
      </h2>
      <span class="text-[11px] font-mono text-slate-400">tbl_sk_...</span>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <div>
        <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Key Name</label>
        <input id="ukey-name" type="text" placeholder="My App AI Key" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Allowed Models</label>
        <input id="ukey-models" type="text" value="*" placeholder="* or chat,image,voice,music" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm font-mono text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Token Quota (max 100,000)</label>
        <input id="ukey-tokens" type="number" min="1000" max="100000" value="50000" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div>
        <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Request Quota (max 1,000)</label>
        <input id="ukey-reqs" type="number" min="10" max="1000" value="500" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
    </div>
    <div class="flex flex-wrap items-center justify-between gap-2 pt-1">
      <p id="ukey-status" class="text-xs text-slate-500 dark:text-slate-400"></p>
      <button type="button" onclick="tblincCreateUserKey()" class="min-h-[42px] inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow-sm transition">
        <i data-lucide="key-round" class="w-4 h-4"></i> Generate AI Key
      </button>
    </div>
  </section>

  <section data-motion="card" class="lg:col-span-5 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-3 shadow-sm">
    <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
      <i data-lucide="terminal" class="w-5 h-5 text-indigo-500"></i> Quick API Usage
    </h2>
    <p class="text-xs text-slate-500 dark:text-slate-400">Authenticate requests to any of the built-in AI endpoints with your personal <code>X-API-Key</code> or <code>Authorization: Bearer</code> header:</p>
    <pre class="rounded-xl bg-slate-900 dark:bg-slate-950 border border-slate-800 p-3.5 text-[11px] font-mono text-emerald-300 overflow-x-auto leading-relaxed">curl -X POST http://127.0.0.1:8000/api/ai/chat \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: tbl_sk_YOUR_KEY" \\
  -d '{"message": "Hello tblinc AI!"}'</pre>
    <div class="text-[11px] text-slate-500 dark:text-slate-400">
      Active Studio Key: <code id="profile-active-studio-key" class="text-indigo-600 dark:text-indigo-400">None selected</code>
    </div>
  </section>
</div>

<!-- Personal AI Keys Table -->
<section data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i> My AI API Keys
    </h2>
    <span class="text-xs text-slate-500">{{ summary.total_keys }} keys</span>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[740px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Name</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Key</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Models</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Tokens Used / Quota</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Status</th>
          <th class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for k in user_keys %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <td class="px-4 sm:px-6 py-3.5 font-semibold text-slate-900 dark:text-white">{{ k.name }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-slate-600 dark:text-slate-300">{{ k.masked_key }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-slate-500">{{ k.allowed_models }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs">
            <div>{{ k.tokens_used }} / {{ k.token_quota }} ({{ k.requests_used }} reqs)</div>
            <div class="mt-1 h-1.5 w-28 rounded-full bg-slate-200 dark:bg-slate-800 overflow-hidden">
              <div class="h-full bg-emerald-500" style="width: {{ k.token_pct }}%"></div>
            </div>
          </td>
          <td class="px-4 sm:px-6 py-3.5">
            {% if k.is_active %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">Active</span>
            {% else %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300">Paused</span>
            {% endif %}
          </td>
          <td class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap space-x-1">
            <button type="button" onclick="tblincRevealUserKey({{ k.id }}, false)" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-500/20">Copy</button>
            <button type="button" onclick="tblincRevealUserKey({{ k.id }}, true)" class="px-2.5 py-1 rounded-lg bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 text-xs font-medium hover:bg-indigo-100">Use in Studio</button>
            <button type="button" onclick="tblincToggleUserKey({{ k.id }})" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-medium hover:bg-amber-100 dark:hover:bg-amber-500/20">Toggle</button>
            <button type="button" onclick="tblincRotateUserKey({{ k.id }})" class="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-xs font-medium hover:bg-cyan-100 dark:hover:bg-cyan-500/20">Rotate</button>
            <button type="button" onclick="tblincDeleteUserKey({{ k.id }})" class="px-2.5 py-1 rounded-lg bg-rose-50 dark:bg-rose-500/15 text-rose-700 dark:text-rose-300 text-xs font-medium hover:bg-rose-100">Delete</button>
          </td>
        </tr>
        {% empty %}
        <tr><td colspan="6" class="px-6 py-8 text-center text-xs text-slate-500">No personal AI keys yet. Generate your first key above.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<!-- Recent Personal Usage Logs -->
<section data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="bar-chart-3" class="w-4 h-4 text-cyan-500"></i> My Recent Token Usage
    </h2>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[640px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3 whitespace-nowrap">Model</th>
          <th class="px-4 sm:px-6 py-3 whitespace-nowrap">Key</th>
          <th class="px-4 sm:px-6 py-3 whitespace-nowrap">Prompt</th>
          <th class="px-4 sm:px-6 py-3 whitespace-nowrap">Completion</th>
          <th class="px-4 sm:px-6 py-3 whitespace-nowrap">Total</th>
          <th class="px-4 sm:px-6 py-3 whitespace-nowrap">Latency</th>
          <th class="px-4 sm:px-6 py-3 text-right whitespace-nowrap">Status</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for u in recent_usage %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <td class="px-4 sm:px-6 py-3"><code class="px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-500/15 text-indigo-700 dark:text-indigo-300 text-xs">{{ u.model_key }}</code></td>
          <td class="px-4 sm:px-6 py-3 text-slate-700 dark:text-slate-200">{{ u.key_name }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs">{{ u.prompt_tokens }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs">{{ u.completion_tokens }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono font-semibold text-xs text-slate-900 dark:text-white">{{ u.total_tokens }}</td>
          <td class="px-4 sm:px-6 py-3 font-mono text-xs text-slate-500">{{ u.latency_ms }} ms</td>
          <td class="px-4 sm:px-6 py-3 text-right font-mono text-xs text-emerald-600 dark:text-emerald-400">{{ u.status }}</td>
        </tr>
        {% empty %}
        <tr><td colspan="7" class="px-6 py-8 text-center text-xs text-slate-500">No AI requests recorded yet. Run any AI chat, image, video, audio, or music tool to see live usage here.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>

<!-- Account Profile & Password Forms -->
<div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
  <section data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
      <i data-lucide="user" class="w-4 h-4 text-indigo-500"></i> Profile Details
    </h2>
    <form method="post" action="/profile/update/" class="space-y-3">
      {% csrf_token %}
      <div>
        <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Username</label>
        <input type="text" value="{{ profile_user.username }}" disabled class="w-full rounded-xl bg-slate-100 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 px-3 py-2 text-sm text-slate-500">
      </div>
      <div>
        <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Email Address</label>
        <input type="email" name="email" value="{{ profile_user.email }}" placeholder="you@example.com" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <button type="submit" class="min-h-[40px] inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition">
        <i data-lucide="save" class="w-4 h-4"></i> Save Email
      </button>
    </form>
  </section>

  <section data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
      <i data-lucide="lock" class="w-4 h-4 text-rose-500"></i> Change Password
    </h2>
    <form method="post" action="/profile/password/" class="space-y-3">
      {% csrf_token %}
      <div>
        <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Current Password</label>
        <input type="password" name="current_password" required class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">New Password</label>
          <input type="password" name="new_password" minlength="6" required class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Confirm New Password</label>
          <input type="password" name="confirm_password" minlength="6" required class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
        </div>
      </div>
      <button type="submit" class="min-h-[40px] inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-semibold transition">
        <i data-lucide="shield-check" class="w-4 h-4"></i> Update Password
      </button>
    </form>
  </section>
</div>
{% endblock %}
{% block scripts %}
<script>
function tblincRefreshActiveStudioKeyBadge() {
  const el = document.getElementById("profile-active-studio-key");
  if (!el) return;
  const k = (localStorage.getItem("tblinc-user-api-key") || "").trim();
  el.textContent = k ? (k.slice(0, 10) + "••••" + k.slice(-4)) : "None selected";
}
function tblincShowKeyBanner(title, rawKey) {
  const box = document.getElementById("user-key-reveal-box");
  const ttl = document.getElementById("user-key-reveal-title");
  const val = document.getElementById("user-key-reveal-val");
  if (!box || !val) return;
  if (ttl) ttl.textContent = title;
  val.textContent = rawKey;
  box.classList.remove("hidden");
  box.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
window.tblincCopyRevealedKey = function () {
  const val = (document.getElementById("user-key-reveal-val") || {}).textContent || "";
  if (val && navigator.clipboard) {
    navigator.clipboard.writeText(val).then(() => tblincSiteToast("Copied AI key to clipboard"));
  }
};
window.tblincActivateRevealedKey = function () {
  const val = ((document.getElementById("user-key-reveal-val") || {}).textContent || "").trim();
  if (!val) return;
  localStorage.setItem("tblinc-user-api-key", val);
  tblincRefreshActiveStudioKeyBadge();
  tblincSiteToast("Active tblinc AI key saved!");
};
window.tblincCreateUserKey = async function () {
  const status = document.getElementById("ukey-status");
  status.textContent = "Generating AI key...";
  const resp = await fetch("/api/user/keys", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      name: document.getElementById("ukey-name").value,
      allowed_models: document.getElementById("ukey-models").value || "*",
      token_quota: parseInt(document.getElementById("ukey-tokens").value || "50000", 10),
      request_quota: parseInt(document.getElementById("ukey-reqs").value || "500", 10)
    })
  });
  const data = await resp.json();
  if (resp.ok && data.key) {
    tblincShowKeyBanner("New Personal AI Key: " + data.key.name, data.key.api_key);
    localStorage.setItem("tblinc-user-api-key", data.key.api_key);
    tblincRefreshActiveStudioKeyBadge();
    status.textContent = "Key created and activated for tblinc AI.";
    setTimeout(() => window.location.reload(), 1400);
  } else {
    status.textContent = "Error: " + (data.error || "Failed to generate key");
  }
};
window.tblincRevealUserKey = async function (id, activateStudio) {
  const resp = await fetch("/api/user/keys/" + id + "/reveal", { method: "POST" });
  const data = await resp.json();
  if (!resp.ok || !data.api_key) { tblincSiteToast(data.error || "Failed to load key"); return; }
  tblincShowKeyBanner("AI Key: " + data.name, data.api_key);
  if (activateStudio) {
    localStorage.setItem("tblinc-user-api-key", data.api_key);
    tblincRefreshActiveStudioKeyBadge();
    tblincSiteToast("Activated '" + data.name + "' for tblinc AI!");
  } else if (navigator.clipboard) {
    navigator.clipboard.writeText(data.api_key).then(() => tblincSiteToast("Copied '" + data.name + "' to clipboard"));
  }
};
window.tblincToggleUserKey = async function (id) {
  await fetch("/api/user/keys/" + id + "/toggle", { method: "POST" });
  window.location.reload();
};
window.tblincRotateUserKey = async function (id) {
  if (!confirm("Rotate this AI key? The previous key value will stop working immediately.")) return;
  const resp = await fetch("/api/user/keys/" + id + "/rotate", { method: "POST" });
  const data = await resp.json();
  if (resp.ok && data.key) {
    tblincShowKeyBanner("Rotated AI Key: " + data.key.name, data.key.api_key);
    localStorage.setItem("tblinc-user-api-key", data.key.api_key);
    tblincRefreshActiveStudioKeyBadge();
    tblincSiteToast("Key rotated!");
  }
};
window.tblincDeleteUserKey = async function (id) {
  if (!confirm("Delete this personal AI key permanently?")) return;
  await fetch("/api/user/keys/" + id, { method: "DELETE" });
  window.location.reload();
};
tblincRefreshActiveStudioKeyBadge();
</script>
{% endblock %}
"""

USER_SETTINGS_TEMPLATE = """{% extends "tblinc_site_base.html" %}
{% block title %}Settings · {{ site_title|default:"tblinc AI" }}{% endblock %}
{% block site_content %}
<div data-motion="hero" class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
  <div>
    <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
      <i data-lucide="settings" class="w-6 h-6 text-indigo-500"></i> Workspace Settings
    </h1>
    <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">Customize appearance, sidenav layout, default AI tab, and your personal tblinc AI API key.</p>
  </div>
  {% if user %}
  <a href="/profile/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition shrink-0">
    <i data-lucide="key-round" class="w-4 h-4"></i> Manage My AI Keys
  </a>
  {% else %}
  <a href="/auth/register/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition shrink-0">
    <i data-lucide="user-plus" class="w-4 h-4"></i> Sign Up &amp; Get AI Key
  </a>
  {% endif %}
</div>

<div class="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
  <!-- Left: Workspace Preferences & Studio Key -->
  <section data-motion="card" class="lg:col-span-8 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-6 shadow-sm">
    <div class="space-y-3">
      <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">Appearance &amp; Navigation</h2>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Theme Mode</label>
          <select id="uset-theme" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
            <option value="system">System Default</option>
            <option value="light">Light Theme</option>
            <option value="dark">Dark Theme</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Desktop Sidenav</label>
          <select id="uset-sidenav" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
            <option value="expanded">Expanded (Labels + Icons)</option>
            <option value="mini">Icon Only (Compact)</option>
          </select>
        </div>
        <div>
          <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Default AI Tab</label>
          <select id="uset-tab" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
            <option value="chat">AI Chat</option>
            <option value="images">AI Images</option>
            <option value="video">AI Video</option>
            <option value="audio">AI Audio</option>
            <option value="music">AI Music</option>
          </select>
        </div>
      </div>
    </div>

    <div class="space-y-3 pt-4 border-t border-slate-200 dark:border-slate-800">
      <div class="flex items-center justify-between gap-2">
        <h2 class="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">tblinc AI API Key (X-API-Key)</h2>
        {% if user %}
        <a href="/profile/" class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline">Open Profile Keys &rarr;</a>
        {% endif %}
      </div>
      <p class="text-xs text-slate-500 dark:text-slate-400">Saved locally in your browser and automatically sent in the <code>X-API-Key</code> header when you run AI Chat, Images, Video, Audio, or Music.</p>
      <div class="flex flex-col sm:flex-row gap-2">
        <input id="uset-api-key" type="password" placeholder="tbl_sk_..." class="flex-1 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm font-mono text-slate-900 dark:text-slate-100">
        <button type="button" onclick="tblincClearUserApiKey()" class="px-3.5 py-2 rounded-xl border border-slate-300 dark:border-slate-700 text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800">Clear</button>
      </div>
      {% if user_keys %}
      <div class="flex flex-wrap items-center gap-2 pt-1">
        <span class="text-[11px] text-slate-500">Quick-load from your profile:</span>
        {% for k in user_keys %}
        <button type="button" onclick="tblincLoadProfileKeyIntoSettings({{ k.id }})" class="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-500/15 border border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-300 text-xs font-medium hover:bg-emerald-100">{{ k.name }}</button>
        {% endfor %}
      </div>
      {% endif %}
    </div>

    <div class="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3">
      <p id="uset-msg" class="text-xs text-slate-500 dark:text-slate-400"></p>
      <button type="button" onclick="tblincSaveUserSettings()" class="w-full sm:w-auto min-h-[42px] inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold shadow-sm transition">
        <i data-lucide="save" class="w-4 h-4"></i> Save Preferences
      </button>
    </div>
  </section>

  <!-- Right: Account & System Info -->
  <section data-motion="card" class="lg:col-span-4 glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-4 shadow-sm">
    <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
      <i data-lucide="user-circle" class="w-5 h-5 text-emerald-500"></i> Account
    </h2>
    {% if user %}
    <div class="space-y-2 text-xs sm:text-sm">
      <div class="font-bold text-slate-900 dark:text-white">{{ user.username }}</div>
      <div class="text-slate-500 dark:text-slate-400">{{ user.email|default:"No email configured" }}</div>
      <div class="pt-2 flex flex-col gap-2">
        <a href="/profile/" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition">
          <i data-lucide="key-round" class="w-4 h-4"></i> Profile &amp; Personal AI Keys
        </a>
        <a href="/auth/logout/" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-rose-600 dark:text-rose-400 text-xs font-semibold hover:bg-rose-50 dark:hover:bg-rose-500/10 transition">
          <i data-lucide="log-out" class="w-4 h-4"></i> Sign Out
        </a>
      </div>
    </div>
    {% else %}
    <p class="text-xs text-slate-500 dark:text-slate-400">Sign in or create a free account to get your own personal <code>tbl_sk_...</code> AI API key and track token usage.</p>
    <div class="flex flex-col gap-2">
      <a href="/auth/register/" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition">
        <i data-lucide="user-plus" class="w-4 h-4"></i> Sign Up
      </a>
      <a href="/auth/login/" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 text-xs font-semibold hover:bg-slate-100 dark:hover:bg-slate-800 transition">
        <i data-lucide="log-in" class="w-4 h-4"></i> Sign In
      </a>
    </div>
    {% endif %}

    <dl class="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-2 text-xs">
      <div class="flex items-center justify-between"><dt class="text-slate-500">Built-in AI Models</dt><dd class="font-mono font-semibold text-indigo-600 dark:text-indigo-400">{{ ai_count }}</dd></div>
      <div class="flex items-center justify-between"><dt class="text-slate-500">Compute</dt><dd class="font-mono uppercase text-slate-700 dark:text-slate-200">{{ hardware.preferred_device }}</dd></div>
      <div class="flex items-center justify-between"><dt class="text-slate-500">Python</dt><dd class="font-mono text-slate-700 dark:text-slate-200">{{ hardware.python_version }}</dd></div>
    </dl>
  </section>
</div>
{% endblock %}
{% block scripts %}
<script>
(function () {
  const savedTheme = localStorage.getItem("tblinc-theme") || "system";
  const savedNav = localStorage.getItem("tblinc-site-sidenav") || "expanded";
  const savedTab = localStorage.getItem("tblinc-default-tab") || "chat";
  const savedKey = localStorage.getItem("tblinc-user-api-key") || "";
  document.getElementById("uset-theme").value = (savedTheme === "dark" || savedTheme === "light") ? savedTheme : "system";
  document.getElementById("uset-sidenav").value = savedNav === "mini" ? "mini" : "expanded";
  document.getElementById("uset-tab").value = savedTab;
  document.getElementById("uset-api-key").value = savedKey;
})();

window.tblincLoadProfileKeyIntoSettings = async function (id) {
  const resp = await fetch("/api/user/keys/" + id + "/reveal", { method: "POST" });
  const data = await resp.json();
  if (resp.ok && data.api_key) {
    document.getElementById("uset-api-key").value = data.api_key;
    localStorage.setItem("tblinc-user-api-key", data.api_key);
    tblincSiteToast("Loaded '" + data.name + "' into AI Studio!");
  }
};

window.tblincClearUserApiKey = function () {
  document.getElementById("uset-api-key").value = "";
  localStorage.removeItem("tblinc-user-api-key");
  tblincSiteToast("Cleared saved AI Studio key");
};

window.tblincSaveUserSettings = function () {
  const theme = document.getElementById("uset-theme").value;
  const nav = document.getElementById("uset-sidenav").value;
  const tab = document.getElementById("uset-tab").value;
  const key = (document.getElementById("uset-api-key").value || "").trim();

  if (theme === "system") {
    localStorage.removeItem("tblinc-theme");
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.classList.toggle("dark", prefersDark);
  } else {
    localStorage.setItem("tblinc-theme", theme);
    document.documentElement.classList.toggle("dark", theme === "dark");
  }
  if (window.tblincSyncThemeUI) window.tblincSyncThemeUI();
  if (window.tblincApplySiteSidenav) window.tblincApplySiteSidenav(nav);
  localStorage.setItem("tblinc-default-tab", tab);
  if (key) { localStorage.setItem("tblinc-user-api-key", key); } else { localStorage.removeItem("tblinc-user-api-key"); }
  document.getElementById("uset-msg").textContent = "Preferences saved!";
  tblincSiteToast("Workspace settings saved!");
};
</script>
{% endblock %}
"""

USER_BILLING_TEMPLATE = """{% extends "tblinc_site_base.html" %}
{% block title %}Billing, Balance & Transactions · {{ site_title|default:"tblinc AI" }}{% endblock %}
{% block site_content %}
<div data-motion="hero" class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
  <div>
    <h1 class="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-2.5">
      <i data-lucide="credit-card" class="w-6 h-6 text-emerald-500"></i> Billing, Balance &amp; Transactions
    </h1>
    <p class="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">Manage your wallet balance, top up token credits, and inspect live AI inference transaction history.</p>
  </div>
  <div class="flex items-center gap-2 shrink-0">
    <a href="/profile/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition">
      <i data-lucide="key-round" class="w-4 h-4 text-emerald-500"></i> My AI Keys
    </a>
    <a href="/" class="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition">
      <i data-lucide="sparkles" class="w-4 h-4"></i> AI Workspace
    </a>
  </div>
</div>

<!-- Billing Summary KPI Cards -->
<section class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between">
      <span>Available Balance</span><i data-lucide="wallet" class="w-4 h-4 text-emerald-500"></i>
    </div>
    <div id="bill-kpi-balance" class="mt-2 text-2xl sm:text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">${{ billing.balance_display }}</div>
    <div class="text-[11px] font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 mt-0.5">{{ billing.plan_tier }} Plan</div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between">
      <span>Total AI Spend</span><i data-lucide="trending-down" class="w-4 h-4 text-rose-500"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">${{ billing.total_spent_display }}</div>
    <div class="text-[11px] text-slate-500 mt-0.5">{{ billing.tokens_used }} tokens consumed</div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between">
      <span>Total Credits Added</span><i data-lucide="arrow-up-circle" class="w-4 h-4 text-cyan-500"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">${{ billing.total_credited_display }}</div>
    <div class="text-[11px] text-slate-500 mt-0.5">{{ billing.transaction_count }} transactions</div>
  </div>
  <div data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm">
    <div class="text-xs font-medium text-slate-500 flex items-center justify-between">
      <span>Token Quota Left</span><i data-lucide="gauge" class="w-4 h-4 text-indigo-500"></i>
    </div>
    <div class="mt-2 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">{{ billing.tokens_remaining }}</div>
    <div class="text-[11px] text-slate-500 mt-0.5">of {{ billing.total_quota }} total quota</div>
  </div>
</section>

<!-- Instant Top-Up Packages & Custom Credit Form -->
<section data-motion="card" class="glass border border-slate-200 dark:border-slate-800 rounded-2xl p-5 sm:p-6 space-y-5 shadow-sm">
  <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
    <div>
      <h2 class="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
        <i data-lucide="plus-circle" class="w-5 h-5 text-emerald-500"></i> Add Funds &amp; Top Up Token Quota
      </h2>
      <p class="text-xs text-slate-500 dark:text-slate-400">Topping up immediately credits your USD balance and increases token &amp; request quotas across all your active AI keys.</p>
    </div>
  </div>

  <!-- 3 Preset Packages -->
  <div class="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
    <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/70 p-4 flex flex-col justify-between gap-3">
      <div>
        <span class="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Starter Pack</span>
        <div class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">+$10.00</div>
        <p class="text-xs text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">+100,000 AI Tokens · +1,000 Requests</p>
      </div>
      <button type="button" onclick="tblincQuickTopUp(10, 'Starter Pack +$10.00 (+100,000 tokens)')" class="w-full min-h-[40px] px-3 py-2 rounded-xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-semibold hover:opacity-90 transition">
        Add $10.00 Credit
      </button>
    </div>

    <div class="rounded-2xl border-2 border-indigo-500 bg-indigo-50/40 dark:bg-indigo-950/30 p-4 flex flex-col justify-between gap-3 relative">
      <div>
        <span class="text-[11px] font-bold uppercase tracking-wider text-indigo-600 dark:text-indigo-400">Pro Pack · Most Popular</span>
        <div class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">+$25.00</div>
        <p class="text-xs text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">+300,000 AI Tokens · +3,000 Requests</p>
      </div>
      <button type="button" onclick="tblincQuickTopUp(25, 'Pro Pack +$25.00 (+300,000 tokens)')" class="w-full min-h-[40px] px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition">
        Add $25.00 Credit (Pro)
      </button>
    </div>

    <div class="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/70 p-4 flex flex-col justify-between gap-3">
      <div>
        <span class="text-[11px] font-semibold uppercase tracking-wider text-cyan-600 dark:text-cyan-400">Scale Pack</span>
        <div class="text-2xl font-extrabold text-slate-900 dark:text-white mt-1">+$100.00</div>
        <p class="text-xs text-emerald-600 dark:text-emerald-400 font-semibold mt-0.5">+1,500,000 AI Tokens · +15,000 Requests</p>
      </div>
      <button type="button" onclick="tblincQuickTopUp(100, 'Scale Pack +$100.00 (+1,500,000 tokens)')" class="w-full min-h-[40px] px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-sm transition">
        Add $100.00 Credit (Scale)
      </button>
    </div>
  </div>

  <!-- Custom Amount Form -->
  <div class="pt-3 border-t border-slate-200 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-12 gap-3 items-end">
    <div class="sm:col-span-4">
      <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Custom Amount (USD)</label>
      <input id="bill-custom-amt" type="number" min="1" max="10000" step="1" value="50" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
    </div>
    <div class="sm:col-span-4">
      <label class="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Payment Method</label>
      <select id="bill-method" class="w-full rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 px-3 py-2 text-sm text-slate-900 dark:text-slate-100">
        <option value="Card •••• 4242">Card •••• 4242</option>
        <option value="Developer Credits">Developer Credits</option>
        <option value="Enterprise Invoice">Enterprise Invoice</option>
      </select>
    </div>
    <div class="sm:col-span-4">
      <button type="button" onclick="tblincCustomTopUp()" class="w-full min-h-[40px] inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-sm transition">
        <i data-lucide="plus" class="w-4 h-4"></i> Top Up Custom Amount
      </button>
    </div>
  </div>
  <p id="bill-status" class="text-xs text-slate-500 dark:text-slate-400"></p>
</section>

<!-- Full Transactions History Table -->
<section data-motion="card" class="w-full glass border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
  <div class="px-4 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
    <h2 class="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
      <i data-lucide="receipt" class="w-4 h-4 text-indigo-500"></i> Billing &amp; Usage Transactions
    </h2>
    <span class="text-xs text-slate-500">{{ billing.transaction_count }} records</span>
  </div>
  <div class="w-full overflow-x-auto">
    <table class="w-full min-w-[760px] text-left text-xs sm:text-sm">
      <thead class="bg-slate-100 dark:bg-slate-900/90 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
        <tr>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Reference</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Type</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Description</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Tokens Added</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Amount</th>
          <th class="px-4 sm:px-6 py-3.5 whitespace-nowrap">Balance After</th>
          <th class="px-4 sm:px-6 py-3.5 text-right whitespace-nowrap">Date</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200 dark:divide-slate-800/70">
        {% for tx in transactions %}
        <tr class="hover:bg-slate-50 dark:hover:bg-slate-800/40">
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-slate-500">{{ tx.reference_id }}</td>
          <td class="px-4 sm:px-6 py-3.5">
            {% if tx.is_credit %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 uppercase">{{ tx.tx_type }}</span>
            {% else %}
            <span class="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-300 uppercase">{{ tx.tx_type }}</span>
            {% endif %}
          </td>
          <td class="px-4 sm:px-6 py-3.5 text-slate-700 dark:text-slate-200">{{ tx.description }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-indigo-600 dark:text-indigo-400">{% if tx.tokens_added %}+{{ tx.tokens_added }}{% else %}&mdash;{% endif %}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono font-semibold text-xs {% if tx.is_credit %}text-emerald-600 dark:text-emerald-400{% else %}text-rose-600 dark:text-rose-400{% endif %}">{{ tx.amount_display }}</td>
          <td class="px-4 sm:px-6 py-3.5 font-mono text-xs text-slate-700 dark:text-slate-200">{{ tx.balance_after_display }}</td>
          <td class="px-4 sm:px-6 py-3.5 text-right font-mono text-xs text-slate-500 whitespace-nowrap">{{ tx.created_at }}</td>
        </tr>
        {% empty %}
        <tr><td colspan="7" class="px-6 py-8 text-center text-xs text-slate-500">No billing transactions recorded yet.</td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</section>
{% endblock %}
{% block scripts %}
<script>
window.tblincQuickTopUp = async function (amount, desc) {
  const status = document.getElementById("bill-status");
  const method = (document.getElementById("bill-method") || {}).value || "Card •••• 4242";
  status.textContent = "Processing top-up...";
  const resp = await fetch("/api/user/billing/topup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ amount_usd: amount, payment_method: method, description: desc })
  });
  const data = await resp.json();
  if (resp.ok) {
    tblincSiteToast("Added $" + amount.toFixed(2) + " to your balance!");
    setTimeout(() => window.location.reload(), 650);
  } else {
    status.textContent = "Error: " + (data.error || "Top-up failed");
  }
};
window.tblincCustomTopUp = function () {
  const amt = parseFloat(document.getElementById("bill-custom-amt").value || "25");
  if (!amt || amt < 1) { tblincSiteToast("Enter at least $1.00"); return; }
  window.tblincQuickTopUp(amt, "");
};
</script>
{% endblock %}
"""

