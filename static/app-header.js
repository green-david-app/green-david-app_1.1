// Unified Header Component
class AppHeader {
  constructor() {
    this.render();
    this.cleanupLegacyHeaders();
    this.initBackButton();
    // initSearch() removed - using global-search.js instead
    this.ensureGlobalSearchAssets();
    this.initUserBox();
    // Dynamic header height tracking
    this.updateHeaderHeight();
    this.initResizeObserver();
  }

  // Měří reálnou výšku headeru a nastaví CSS proměnné
  updateHeaderHeight() {
    const header = document.getElementById('app-header');
    if (!header) return;
    
    const height = header.offsetHeight;
    const gap = 16; // --page-top-gap
    const offset = height + gap;
    
    document.documentElement.style.setProperty('--app-header-h', height + 'px');
    document.documentElement.style.setProperty('--app-header-offset', offset + 'px');
  }

  // ResizeObserver pro sledování změn velikosti headeru
  initResizeObserver() {
    const header = document.getElementById('app-header');
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
        const headerHTML = `
<header class="app-header">
  <div class="app-header-container">
    <button class="app-header-back" id="app-header-back" type="button" title="Zpět">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M15 18l-6-6 6-6"/>
      </svg>
      <span class="app-header-back-label">Zpět</span>
    </button>

    <a href="/" class="app-header-brand">
      <img src="/logo.jpg" alt="green david app" class="app-header-logo" onerror="this.src='/logo.svg'"/>
      <div class="app-header-text">
        <div class="app-header-title">green david app</div>
        <div class="app-header-subtitle">interní systém</div>
      </div>
    </a>

    <div class="global-search-container"></div>

    <div class="app-header-actions">
      <div id="userbox" class="app-header-user"></div>

      <a href="/notifications.html" class="app-header-notifications" title="Notifikace" aria-label="Notifikace">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
        <span id="notif-badge" class="notif-badge" style="display:none">0</span>
      </a>

      <a href="/settings.html" class="app-header-settings" title="Nastavení">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M19.4 15a7.9 7.9 0 0 0 .1-1 7.9 7.9 0 0 0-.1-1l2-1.5-2-3.5-2.4 1a8.2 8.2 0 0 0-1.7-1L15 2H9l-.3 3a8.2 8.2 0 0 0-1.7 1l-2.4-1-2 3.5 2 1.5a7.9 7.9 0 0 0-.1 1 7.9 7.9 0 0 0 .1 1l-2 1.5 2 3.5 2.4-1a8.2 8.2 0 0 0 1.7 1L9 22h6l.3-3a8.2 8.2 0 0 0 1.7-1l2.4 1 2-3.5-2-1.5Z"></path>
        </svg>
      </a>
    </div>
  </div>
</header>
        `;

        const existingHeader = document.querySelector('.app-header');
        if (existingHeader) {
          existingHeader.outerHTML = headerHTML;
          return;
        }

        // Vložit header jako první element v body
        document.body.insertAdjacentHTML('afterbegin', headerHTML);
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
    const box = document.getElementById("userbox");
    if (!box) {
      // Pokud userbox neexistuje, počkat a zkusit znovu
      setTimeout(() => this.initUserBox(), 100);
      return;
    }

    try {
      const res = await fetch("/api/me", { credentials: "same-origin" });
      const j = await res.json();
      
      if (j.authenticated) {
        const u = j.user || {};
        const nameOrEmail = (u.name || u.email || 'Uživatel').toString();
        const role = (u.role || '').toString();
        box.innerHTML = `
          <span title="${nameOrEmail}${role ? ' (' + role + ')' : ''}">
            <strong style="color:#e8eef2;">${nameOrEmail}</strong>
            ${role ? `<span style="color:#9ca8b3;">&nbsp;(${role})</span>` : ''}
          </span>
          <span>Úkoly: <strong style="color:#e8eef2;">${j.tasks_count || 0}</strong></span>
          <button class="btn btn-ghost btn-sm" id="logout-btn" style="padding:6px 12px;font-size:13px;">Odhlásit</button>
        `;
        
        // Přidat event listener pro logout tlačítko
        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
          logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Update notifications badge
        try {
          const cnt = Number(j.unread_notifications || 0) || 0;
          const badge = document.getElementById('notif-badge');
          if (badge) {
            badge.textContent = String(cnt);
            badge.style.display = cnt > 0 ? 'inline-flex' : 'none';
          }
        } catch (_) {}
      } else {
        box.innerHTML = '<span style="color:#9ca8b3;">Nepřihlášen</span>';
      }
    } catch (e) {
      console.error('UserBox error:', e);
      box.innerHTML = '';
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

