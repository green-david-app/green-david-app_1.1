// Unified Header Component
class AppHeader {
  constructor() {
    this.render();
    this.cleanupLegacyHeaders();
    this.initBackButton();
    this.initSidebarToggle();
    this.ensureGlobalSearchAssets();
    this.initUserBox();
    this.initAIOperator();
    this.updateHeaderHeight();
    this.initResizeObserver();
    this.updatePageTitle();
  }
  
  initSidebarToggle() {
    const toggle = document.getElementById('app-header-sidebar-toggle');
    if (toggle) {
      toggle.addEventListener('click', () => {
        if (window.appSidebar) {
          window.appSidebar.toggle();
        }
      });
    }
  }
  
  updatePageTitle() {
    const titleEl = document.getElementById('app-header-page-title');
    if (!titleEl) return;
    
    // Fallback mapa podle URL — nejspolehlivější
    const path = window.location.pathname;
    const titles = {
      '/': 'Přehled',
      '/index.html': 'Přehled',
      '/jobs.html': 'Zakázky',
      '/jobs': 'Zakázky',
      '/tasks.html': 'Úkoly',
      '/tasks': 'Úkoly',
      '/calendar.html': 'Kalendář',
      '/calendar': 'Kalendář',
      '/timesheets.html': 'Výkazy',
      '/timesheets': 'Výkazy',
      '/warehouse.html': 'Sklad',
      '/warehouse': 'Sklad',
      '/materials.html': 'Materiál',
      '/finance.html': 'Finance',
      '/finance': 'Finance',
      '/team.html': 'Tým',
      '/employees.html': 'Zaměstnanci',
      '/reports.html': 'Reporty',
      '/reports-hub.html': 'Reporty',
      '/reports-daily.html': 'Denní report',
      '/reports-week.html': 'Týdenní report',
      '/reports-project.html': 'Projektový report',
      '/settings.html': 'Nastavení',
      '/settings': 'Nastavení',
      '/documents.html': 'Dokumenty',
      '/notifications.html': 'Notifikace',
      '/nursery.html': 'Školka',
      '/plant-database.html': 'Databáze rostlin',
      '/planning-daily.html': 'Plánování',
      '/planning-timeline.html': 'Timeline plánování',
      '/planning-week.html': 'Týdenní plán',
      '/planning-costs.html': 'Náklady',
      '/timeline.html': 'Timeline',
      '/ai-operator.html': 'AI Operátor',
      '/inbox.html': 'Inbox',
      '/issues.html': 'Problémy',
      '/recurring-tasks.html': 'Opakované úkoly',
      '/jobs-new.html': 'Nová zakázka',
      '/job-detail.html': 'Detail zakázky',
      '/employee-detail.html': 'Detail zaměstnance'
    };
    
    // Nejdřív zkusit URL mapu
    if (titles[path]) {
      titleEl.textContent = titles[path];
      return;
    }
    
    // Pak zkusit <title> tag
    const pageTitle = document.title
      .replace(/\s*[-–|]\s*green david app/i, '')
      .replace(/^green david app$/i, '')
      .trim();
    
    if (pageTitle && pageTitle.toLowerCase() !== 'green david app' && pageTitle.toLowerCase() !== 'green david') {
      titleEl.textContent = pageTitle;
      return;
    }
    
    // Fallback
    titleEl.textContent = 'Green David';
  }

  // Měří reálnou výšku headeru a nastaví CSS proměnné
  updateHeaderHeight() {
    const header = document.querySelector('header.app-header');
    if (!header) return;
    
    const height = header.offsetHeight;
    const gap = 16; // --page-top-gap
    const offset = height + gap;
    
    document.documentElement.style.setProperty('--app-header-h', height + 'px');
    document.documentElement.style.setProperty('--app-header-offset', offset + 'px');
  }

  // ResizeObserver pro sledování změn velikosti headeru
  initResizeObserver() {
    const header = document.querySelector('header.app-header');
    if (!header || typeof ResizeObserver === 'undefined') return;
    
    const observer = new ResizeObserver(() => {
      this.updateHeaderHeight();
    });
    
    observer.observe(header);
    window.addEventListener('resize', () => this.updateHeaderHeight());
  }

  ensureGlobalSearchAssets() {
    // Zajistí, že globální vyhledávání funguje na VŠECH stránkách,
    // i když některé HTML soubory nezahrnují global-search.css/js.
    try {
      // CSS
      const cssHref = '/static/css/global-search.css';
      const hasCss = Array.from(document.styleSheets || []).some((s) => {
        try { return (s.href || '').includes(cssHref); } catch (_) { return false; }
      });
      if (!hasCss && !document.querySelector(`link[href="${cssHref}"]`)) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = cssHref;
        document.head.appendChild(link);
      }

      // JS
      const jsSrc = '/static/global-search.js';
      const hasScript = !!document.querySelector(`script[src="${jsSrc}"]`);
      if (!hasScript) {
        const s = document.createElement('script');
        s.src = jsSrc;
        s.defer = true;
        document.head.appendChild(s);
      } else {
        // Pokud je script už načtený, ale instance nevznikla (např. protože container nebyl v DOMu),
        // zkusíme ji vytvořit.
        if (!window.globalSearch && typeof window.GlobalSearch === 'function') {
          try { window.globalSearch = new window.GlobalSearch(); } catch (_) {}
        }
      }
      
      // AI Operator Drawer - globální vrstva
      const aiOpSrc = '/static/js/ai-operator-drawer.js';
      const hasAiOp = !!document.querySelector(`script[src="${aiOpSrc}"]`);
      if (!hasAiOp) {
        const aiScript = document.createElement('script');
        aiScript.src = aiOpSrc;
        aiScript.defer = true;
        document.head.appendChild(aiScript);
      }
      
      // AI Inline Indicators - badge na kartách
      const aiIndSrc = '/static/js/ai-inline-indicators.js';
      const hasAiInd = !!document.querySelector(`script[src="${aiIndSrc}"]`);
      if (!hasAiInd) {
        const indScript = document.createElement('script');
        indScript.src = aiIndSrc;
        indScript.defer = true;
        document.head.appendChild(indScript);
      }
    } catch (e) {
      // no-op
    }
  }

  initBackButton() {
    const btn = document.getElementById('app-header-back');
    if (!btn) return;

    const path = (location.pathname || '/').toLowerCase();
    const isHome = path === '/' || path.endsWith('/index.html');
    const hasHistory = (typeof history !== 'undefined') && (history.length > 1);

    // On home we hide it to avoid a "dead" back button.
    if (isHome && !hasHistory) {
      btn.style.display = 'none';
      return;
    }

    btn.addEventListener('click', (e) => {
      e.preventDefault();
      try {
        if (hasHistory) {
          history.back();
          return;
        }
      } catch (_) {
        // ignore
      }
      // Fallback
      location.href = '/';
    });
  }

  initSearch() {
    const header = document.querySelector('.app-header');
    const form = document.getElementById('app-header-search-form');
    const input = document.getElementById('app-header-search-input');
    const toggle = document.getElementById('app-header-search-toggle');
    if (!header || !form || !input) return;

    // Prefill from URL on search page.
    try {
      const url = new URL(location.href);
      const q = (url.searchParams.get('q') || '').trim();
      if (q) input.value = q;
    } catch (_) {
      // ignore
    }

    const openMobileSearch = () => {
      header.classList.add('search-open');
      // Allow CSS to apply before focusing
      setTimeout(() => input.focus(), 0);
    };

    const closeMobileSearch = () => {
      header.classList.remove('search-open');
      input.blur();
    };

    if (toggle) {
      toggle.addEventListener('click', (e) => {
        e.preventDefault();
        openMobileSearch();
      });
    }

    // Submit -> navigate to unified search page.
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = (input.value || '').trim();
      if (!q) return;
      location.href = `/search.html?q=${encodeURIComponent(q)}`;
    });

    // Esc closes mobile search.
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && header.classList.contains('search-open')) {
        closeMobileSearch();
      }
    });

    // Click outside closes on mobile.
    document.addEventListener('click', (e) => {
      if (!header.classList.contains('search-open')) return;
      const t = e.target;
      if (t && (t.closest('#app-header-search-form') || t.closest('#app-header-search-toggle'))) return;
      closeMobileSearch();
    });
  }


      render() {
        // Smaž jakýkoliv existující header (Jinja2 komponenta nebo starý)
        document.querySelectorAll('.app-header, header.app-header').forEach(el => el.remove());

        const isDesktop = window.innerWidth > 768;
        const hasSidebar = document.body.classList.contains('has-sidebar');

        const headerEl = document.createElement('header');
        headerEl.className = 'app-header';
        // INLINE STYLES as ultimate backup - CSS should handle this but just in case
        headerEl.style.cssText = 'position:fixed !important; top:12px; z-index:1000;';

        headerEl.innerHTML = `
  <div class="app-header-container">
    ${hasSidebar && isDesktop ? `
    <button class="app-header-sidebar-toggle" id="app-header-sidebar-toggle" type="button" title="Toggle sidebar">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
    </button>
    <div class="app-header-page-title" id="app-header-page-title"></div>
    ` : `
    <button class="app-header-back" id="app-header-back" type="button" title="Zpět">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M15 18l-6-6 6-6"/>
      </svg>
      <span class="app-header-back-label">Zpět</span>
    </button>
    <div class="app-header-page-title" id="app-header-page-title"></div>
    `}

    <div class="app-header-search" id="app-header-search-container">
      <svg class="app-header-search-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input type="text" id="app-header-search-input" class="app-header-search-input" placeholder="Vyhledat v aplikaci..." autocomplete="off">
      <div class="global-search-results" id="global-search-results" style="display:none;"></div>
    </div>

    <div class="app-header-actions">
      <span id="header-tasks-count" class="app-header-tasks-count">Úkoly: <strong>0</strong></span>

      <div class="app-header-ai-operator" id="app-header-ai-operator" style="position:relative;">
        <button class="app-header-icon-btn" id="app-header-ai-toggle" type="button" title="AI Operátor">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7Z"/>
            <path d="M9 12h6"/>
            <path d="M12 9v6"/>
          </svg>
          <span id="ai-operator-badge" class="notif-badge" style="display:none;">0</span>
        </button>
        <div class="ai-operator-dropdown" id="ai-operator-dropdown" style="display:none; position:absolute; top:100%; right:0; margin-top:8px; background:#0d1117; border:1px solid #30363d; border-radius:8px; box-shadow:0 8px 32px rgba(0,0,0,0.3); min-width:300px; max-width:400px; z-index:1001; overflow:hidden;">
          <div style="padding:12px 16px; border-bottom:1px solid rgba(255,255,255,0.1); font-weight:600; font-size:14px; color:#e6edf3;">AI Operátor</div>
          <div id="ai-operator-dropdown-content" style="max-height:400px; overflow-y:auto;">
            <div style="padding:24px 16px; text-align:center; color:#8b949e; font-size:14px;">Načítám...</div>
          </div>
        </div>
      </div>

      <a href="/notifications.html" class="app-header-notifications" title="Notifikace">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 01-3.46 0"/>
        </svg>
        <span id="notif-badge" class="notif-badge" style="display:none">0</span>
      </a>

      <a href="/settings.html" class="app-header-settings" title="Nastavení">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M19.4 15a7.9 7.9 0 0 0 .1-1 7.9 7.9 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a8.2 8.2 0 0 0-1.7-1L15 2H9l-.3 3a8.2 8.2 0 0 0-1.7 1l-2.4-1-2 3.5 2 1.5a7.9 7.9 0 0 0-.1 1 7.9 7.9 0 0 0 .1 1l-2 1.5 2 3.5 2.4-1a8.2 8.2 0 0 0 1.7 1L9 22h6l.3-3a8.2 8.2 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5Z"/>
        </svg>
      </a>

      <a href="/logout" id="header-logout-btn" class="app-header-logout-btn">Odhlásit</a>
    </div>
  </div>
        `;

        // Insert as FIRST child of body — NOT inside any container
        document.body.insertBefore(headerEl, document.body.firstChild);
      }


  ensureHeaderStructure(header) {
    // Zajistit, že subtitle existuje
    const textDiv = header.querySelector('.app-header-text');
    if (textDiv && !textDiv.querySelector('.app-header-subtitle')) {
      const title = textDiv.querySelector('.app-header-title');
      if (title) {
        const subtitle = document.createElement('div');
        subtitle.className = 'app-header-subtitle';
        subtitle.textContent = 'interní systém';
        textDiv.appendChild(subtitle);
      }
    }

    // Zajistit, že userbox existuje
    const actions = header.querySelector('.app-header-actions');
    if (actions && !actions.querySelector('#userbox')) {
      const userbox = document.createElement('div');
      userbox.id = 'userbox';
      userbox.className = 'app-header-user';
      actions.insertBefore(userbox, actions.firstChild);
    }

    // Zajistit, že settings link existuje
    if (actions && !actions.querySelector('.app-header-settings')) {
      const settingsLink = document.createElement('a');
      settingsLink.href = '/settings.html';
      settingsLink.className = 'app-header-settings';
      settingsLink.title = 'Nastavení';
      settingsLink.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z"/>
          <path d="M19.4 15a7.9 7.9 0 0 0 .1-1 7.9 7.9 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a8.2 8.2 0 0 0-1.7-1L15 3h-6l-.3 3a8.2 8.2 0 0 0-1.7 1l-2.4-1-2 3.5 2 1.5a7.9 7.9 0 0 0-.1 1 7.9 7.9 0 0 0 .1 1l-2 1.5 2 3.5 2.4-1a8.2 8.2 0 0 0 1.7 1L9 21h6l.3-3a8.2 8.2 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5Z"/>
        </svg>
      `;
      actions.appendChild(settingsLink);
    }
  }

  cleanupLegacyHeaders() {
    // Bezpečně skryj staré top-bary/hlavičky napříč stránkami bez použití CSS :has()
    try {
      const candidates = document.querySelectorAll('.header, .page-header, .brand, .topbar, .top-bar, .top-nav, .navbar, .nav-top');
      candidates.forEach((el) => {
        if (!el.closest('.app-header')) {
          // Pokud je to brand uvnitř nového headeru, nechat být; jinak skrýt
          el.style.display = 'none';
        }
      });
    } catch (e) {
      // no-op
    }
  }

  async initUserBox() {
    try {
      const res = await fetch("/api/me", { credentials: "same-origin" });
      const j = await res.json();
      
      if (j.authenticated) {
        // Update tasks count
        const tasksEl = document.getElementById('header-tasks-count');
        if (tasksEl) {
          tasksEl.innerHTML = `Úkoly: <strong>${j.tasks_count || 0}</strong>`;
        }

        // Update notifications badge
        const badge = document.getElementById('notif-badge');
        if (badge) {
          const cnt = Number(j.unread_notifications || 0) || 0;
          badge.textContent = String(cnt);
          badge.style.display = cnt > 0 ? 'inline-flex' : 'none';
        }

        // Logout handler
        const logoutBtn = document.getElementById('header-logout-btn');
        if (logoutBtn) {
          logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            this.handleLogout();
          });
        }
      }
    } catch (e) {
      // no-op
    }
  }

  initAIOperator() {
    const aiToggle = document.getElementById('app-header-ai-toggle');
    const aiDropdown = document.getElementById('ai-operator-dropdown');
    if (!aiToggle || !aiDropdown) return;

    aiToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = aiDropdown.style.display !== 'none';
      aiDropdown.style.display = isOpen ? 'none' : 'block';
      if (!isOpen) this.loadAIOperatorData();
    });

    document.addEventListener('click', (e) => {
      if (!aiToggle.contains(e.target) && !aiDropdown.contains(e.target)) {
        aiDropdown.style.display = 'none';
      }
    });

    // Initial load for badge
    this.loadAIOperatorData();
  }

  async loadAIOperatorData() {
    const contentEl = document.getElementById('ai-operator-dropdown-content');
    if (!contentEl) return;

    try {
      const res = await fetch('/api/jobs/overview');
      const data = await res.json();
      const jobs = data.jobs || [];
      const today = new Date().toISOString().split('T')[0];

      const overdueJobs = jobs.filter(j => {
        const deadline = j.planned_end_date || j.deadline;
        return deadline && deadline < today && !['Dokončeno','completed','archived','cancelled'].includes(j.status);
      });

      const materialIssues = jobs.filter(j => {
        const m = (j.metrics || {}).material || {};
        return m.status === 'missing';
      });

      let html = '';
      let totalCount = overdueJobs.length + materialIssues.length;

      if (overdueJobs.length > 0) {
        html += `<div style="display:flex;gap:12px;padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.05);border-left:3px solid #ef4444;">
          <div style="flex:1;"><div style="font-weight:600;font-size:14px;color:#e6edf3;">${overdueJobs.length} zakázek po termínu</div>
          <div style="font-size:12px;color:#8b949e;">Vyžaduje okamžitou pozornost</div></div></div>`;
      }
      if (materialIssues.length > 0) {
        html += `<div style="display:flex;gap:12px;padding:12px 16px;border-bottom:1px solid rgba(255,255,255,0.05);border-left:3px solid #fbbf24;">
          <div style="flex:1;"><div style="font-weight:600;font-size:14px;color:#e6edf3;">${materialIssues.length} zakázek chybí materiál</div>
          <div style="font-size:12px;color:#8b949e;">Kontrola zásob nutná</div></div></div>`;
      }
      if (!html) {
        html = '<div style="padding:24px 16px;text-align:center;color:#8b949e;font-size:14px;">Vše v pořádku!</div>';
      }

      contentEl.innerHTML = html;
      const badge = document.getElementById('ai-operator-badge');
      if (badge) {
        badge.textContent = totalCount;
        badge.style.display = totalCount > 0 ? 'inline-flex' : 'none';
      }
    } catch (e) {
      contentEl.innerHTML = '<div style="padding:24px 16px;text-align:center;color:#8b949e;">Chyba načítání</div>';
    }
  }

  async handleLogout() {
    try {
      await fetch('/api/logout', { method: 'POST', credentials: 'same-origin' });
      location.reload();
    } catch (e) {
      console.error('Logout error:', e);
    }
  }

  // Metoda pro refresh userboxu (může být volána zvenčí)
  async refreshUserBox() {
    await this.initUserBox();
  }
}

// Auto-init když je DOM ready
let appHeaderInstance = null;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    appHeaderInstance = new AppHeader();
    // Exponovat instanci globálně pro případné použití zvenčí
    window.appHeader = appHeaderInstance;
  });
} else {
  appHeaderInstance = new AppHeader();
  window.appHeader = appHeaderInstance;
}

// Exponovat refreshUserBox globálně pro kompatibilitu s existujícím kódem
window.refreshUserBox = function() {
  if (appHeaderInstance) {
    appHeaderInstance.refreshUserBox();
  }
};

