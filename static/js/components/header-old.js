// Unified Header Component
class AppHeader {
  constructor() {
    this.render();
    this.cleanupLegacyHeaders();
    this.initBackButton();
    this.initSearch();
    this.initUserBox();
  }

  initBackButton() {
    const btn = document.getElementById('app-header-back');
    if (!btn) return;

    const path = (location.pathname || '/').toLowerCase();
    const isHome = path === '/' || path.endsWith('/index.html');
    const hasHistory = (typeof history !== 'undefined') && (history.length > 1);

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
      location.href = '/';
    });
  }

  initSearch() {
    const header = document.querySelector('.app-header');
    const form = document.getElementById('app-header-search-form');
    const input = document.getElementById('app-header-search-input');
    const toggle = document.getElementById('app-header-search-toggle');
    if (!header || !form || !input) return;

    try {
      const url = new URL(location.href);
      const q = (url.searchParams.get('q') || '').trim();
      if (q) input.value = q;
    } catch (_) {
      // ignore
    }

    const openMobileSearch = () => {
      header.classList.add('search-open');
      setTimeout(() => input.focus(), 0);
    };

    const closeMobileSearch = () => {
      header.classList.remove('search-open');
      input.blur();
    };

    // Search toggle už není v novém headeru - search je vždy viditelný
    // Přidat keyboard shortcut (⌘K / Ctrl+K)
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        input.focus();
      }
    });

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = (input.value || '').trim();
      if (!q) return;
      location.href = `/search.html?q=${encodeURIComponent(q)}`;
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && header.classList.contains('search-open')) {
        closeMobileSearch();
      }
    });

    document.addEventListener('click', (e) => {
      if (!header.classList.contains('search-open')) return;
      const t = e.target;
      if (t && (t.closest('#app-header-search-form') || t.closest('#app-header-search-toggle'))) return;
      closeMobileSearch();
    });
  }


      render() {
        // Načíst data pro header (pokud jsou dostupná)
        const tasksCount = window.headerData?.tasks_count || 0;
        const streakCount = window.headerData?.streak_count || 0;
        const notificationsCount = window.headerData?.notifications_count || 0;
        const messagesCount = window.headerData?.messages_count || 0;
        
        const headerHTML = `
<header class="app-header">
  <div class="app-header-container">
    <!-- Levá část -->
    <div class="app-header-left">
      <button class="app-header-back" id="app-header-back" type="button" title="Zpět" onclick="history.back()">
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
    </div>

    <!-- Střední část - Search -->
    <div class="app-header-center">
      <form class="app-header-search" id="app-header-search-form" role="search">
        <input 
          class="app-header-search-input" 
          id="app-header-search-input" 
          type="search" 
          placeholder="Vyhledat v aplikaci… (⌘K)" 
          autocomplete="off" 
        />
      </form>
    </div>

    <!-- Pravá část -->
    <div class="app-header-actions">
      <div id="userbox" class="app-header-user"></div>
      
      <!-- Úkoly počet -->
      <span class="app-header-tasks">
        Úkoly: <strong id="header-tasks-count">${tasksCount}</strong>
      </span>
      
      <!-- Badge s číslem (streak/body/etc) -->
      ${streakCount > 0 ? `
      <div class="app-header-badge green" title="Streak">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
          <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
        </svg>
        <span id="header-streak-count">${streakCount}</span>
      </div>
      ` : ''}
      
      <!-- Notifikace 1 -->
      <a href="/notifications.html" class="app-header-notification" title="Notifikace" aria-label="Notifikace">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
          <path d="M13.73 21a2 2 0 01-3.46 0" />
        </svg>
        ${notificationsCount > 0 ? `<span class="notification-badge" id="header-notif-badge">${notificationsCount}</span>` : ''}
      </a>
      
      <!-- Notifikace 2 (zprávy/chat) -->
      <a href="/messages.html" class="app-header-notification" title="Zprávy" aria-label="Zprávy">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
        </svg>
        ${messagesCount > 0 ? `<span class="notification-badge" id="header-messages-badge">${messagesCount}</span>` : ''}
      </a>
      
      <!-- Odhlásit -->
      <button class="app-header-logout" onclick="logout()" title="Odhlásit se">
        Odhlásit
      </button>
      
      <!-- Settings -->
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
        `;
        
        // Aktualizovat header data
        this.updateHeaderData({
          tasks_count: j.tasks_count || 0,
          streak_count: j.streak_count || 0,
          notifications_count: j.notifications_count || 0,
          messages_count: j.messages_count || 0
        });
        
        // Uložit data pro pozdější použití
        window.headerData = {
          tasks_count: j.tasks_count || 0,
          streak_count: j.streak_count || 0,
          notifications_count: j.notifications_count || 0,
          messages_count: j.messages_count || 0
        };
      } else {
        box.innerHTML = '<span style="color:#9ca8b3;">Nepřihlášen</span>';
      }
    } catch (e) {
      console.error('UserBox error:', e);
      box.innerHTML = '';
    }
  }
  
  updateHeaderData(data) {
    // Aktualizovat tasks count
    const tasksCountEl = document.getElementById('header-tasks-count');
    if (tasksCountEl) {
      tasksCountEl.textContent = data.tasks_count || 0;
    }
    
    // Aktualizovat streak count
    const streakCountEl = document.getElementById('header-streak-count');
    const streakBadge = document.querySelector('.app-header-badge.green');
    if (streakCountEl) {
      streakCountEl.textContent = data.streak_count || 0;
    }
    if (streakBadge) {
      streakBadge.style.display = (data.streak_count > 0) ? 'flex' : 'none';
    }
    
    // Aktualizovat notifications badge
    const notifBadge = document.getElementById('header-notif-badge');
    if (notifBadge) {
      if (data.notifications_count > 0) {
        notifBadge.textContent = data.notifications_count;
        notifBadge.style.display = 'flex';
      } else {
        notifBadge.style.display = 'none';
      }
    }
    
    // Aktualizovat messages badge
    const messagesBadge = document.getElementById('header-messages-badge');
    if (messagesBadge) {
      if (data.messages_count > 0) {
        messagesBadge.textContent = data.messages_count;
        messagesBadge.style.display = 'flex';
      } else {
        messagesBadge.style.display = 'none';
      }
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

// Globální logout funkce pro použití z HTML
window.logout = function() {
  if (appHeaderInstance) {
    appHeaderInstance.handleLogout();
  } else {
    // Fallback pokud instance neexistuje
    fetch('/api/logout', { method: 'POST', credentials: 'same-origin' })
      .then(() => location.reload())
      .catch(() => location.href = '/login.html');
  }
};

// Search modal
window.openSearchModal = function() {
    // Otevřít search modal nebo focus na search
    const modal = document.getElementById('search-modal');
    if (modal) {
        modal.classList.add('open');
    } else {
        // Fallback: focus na search input
        const input = document.getElementById('header-search-input');
        if (input) {
            input.focus();
            input.removeAttribute('readonly');
        }
    }
};

// Keyboard shortcut ⌘K
document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openSearchModal();
    }
});

// Notifikace dropdown
window.toggleNotificationsDropdown = function() {
    const dropdown = document.getElementById('notifications-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('open');
    } else {
        // Fallback: přesměrovat na notifikace stránku
        window.location.href = '/notifications.html';
    }
};
