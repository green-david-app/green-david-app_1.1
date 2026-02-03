// Unified Header Component - DEFINITIVNÍ VERZE
class AppHeader {
  constructor() {
    this.render();
    this.cleanupLegacyHeaders();
    this.initBackButton();
    this.initUserBox();
    this.updateHeaderHeight();
    this.initResizeObserver();
  }

  render() {
    // Načíst data pro header (pokud jsou dostupná)
    const tasksCount = window.headerData?.tasks_count || 0;
    const notificationsCount = window.headerData?.notifications_count || 0;
    const aiOperatorCount = window.headerData?.ai_operator_count || 45;
    
    const headerHTML = `
<header class="app-header">
    <!-- 1. ZPĚT -->
    <button class="header-back" id="app-header-back" type="button" onclick="history.back()" title="Zpět">
        <svg viewBox="0 0 24 24" width="18" height="18">
            <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" fill="currentColor"/>
        </svg>
        <span>Zpět</span>
    </button>
    
    <!-- 2. LOGO + NÁZEV -->
    <a href="/" class="header-brand">
        <img src="/logo.jpg" alt="green david app" class="header-logo" onerror="this.src='/logo.svg'"/>
        <div class="header-brand-text">
            <span class="header-brand-name">green david app</span>
            <span class="header-brand-subtitle">interní systém</span>
        </div>
    </a>
    
    <!-- 3. VYHLEDÁVÁNÍ -->
    <div class="header-search">
        <input 
            type="text" 
            class="header-search-input" 
            id="header-search-input"
            placeholder="Vyhledat v aplikaci... (⌘K)"
            onclick="openSearchModal()"
            readonly
        >
    </div>
    
    <!-- PRAVÁ ČÁST -->
    <div class="header-right">
        <!-- 4. AI OPERÁTOR -->
        <a href="/ai-operator" class="header-ai-operator" title="AI Operátor">
            <svg viewBox="0 0 24 24" width="18" height="18">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93z" fill="currentColor"/>
            </svg>
            <span class="ai-operator-count" id="header-ai-operator-count">${aiOperatorCount}</span>
        </a>
        
        <!-- 5. ÚKOLY -->
        <a href="/tasks" class="header-tasks" title="Úkoly">
            <span>Úkoly:</span>
            <strong id="header-tasks-count">${tasksCount}</strong>
        </a>
        
        <!-- 6. NOTIFIKACE -->
        <button class="header-notifications" onclick="toggleNotificationsDropdown()" title="Notifikace">
            <svg viewBox="0 0 24 24" width="20" height="20">
                <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" fill="currentColor"/>
            </svg>
            ${notificationsCount > 0 ? `<span class="notification-badge" id="header-notif-badge">${notificationsCount}</span>` : ''}
        </button>
        
        <!-- 7. NASTAVENÍ -->
        <a href="/settings.html" class="header-settings" title="Nastavení">
            <svg viewBox="0 0 24 24" width="20" height="20">
                <path d="M19.14 12.94c.04-.31.06-.63.06-.94 0-.31-.02-.63-.06-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58z" fill="currentColor"/>
                <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.5"/>
            </svg>
        </a>
        
        <!-- 8. ODHLÁSIT -->
        <button class="header-logout" onclick="logout()">
            Odhlásit
        </button>
    </div>
</header>
        `;

        // Najít container pro header
        const headerContainer = document.getElementById('app-header');
        const existingHeader = document.querySelector('.app-header');
        
        if (headerContainer && headerContainer.id === 'app-header' && headerContainer.tagName === 'DIV') {
          // Pokud je to div container, vložit header dovnitř
          headerContainer.innerHTML = headerHTML;
        } else if (existingHeader) {
          // Pokud je to existující header element, nahradit ho
          existingHeader.outerHTML = headerHTML;
        } else {
          // Vložit header jako první element v body
          document.body.insertAdjacentHTML('afterbegin', headerHTML);
        }
  }

  cleanupLegacyHeaders() {
    try {
      const candidates = document.querySelectorAll('.header, .page-header, .brand, .topbar, .top-bar, .top-nav, .navbar, .nav-top');
      candidates.forEach((el) => {
        if (!el.closest('.app-header')) {
          el.style.display = 'none';
        }
      });
    } catch (e) {
      // no-op
    }
  }

  initBackButton() {
    const backBtn = document.getElementById('app-header-back');
    if (backBtn) {
      backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        history.back();
      });
    }
  }

  async initUserBox() {
    try {
      const res = await fetch("/api/me", { credentials: "same-origin" });
      const j = await res.json();
      
      if (j.authenticated) {
        // Aktualizovat header data
        window.headerData = {
          tasks_count: j.tasks_count || 0,
          notifications_count: j.unread_notifications || 0,
          ai_operator_count: j.ai_operator_count || 45
        };
        
        // Aktualizovat header prvky
        this.updateHeaderData(window.headerData);
      }
    } catch (e) {
      console.error('UserBox error:', e);
    }
  }

  updateHeaderData(data) {
    // Aktualizovat tasks count
    const tasksCountEl = document.getElementById('header-tasks-count');
    if (tasksCountEl) {
      tasksCountEl.textContent = data.tasks_count || 0;
    }
    
    // Aktualizovat AI operátor count
    const aiOperatorCountEl = document.getElementById('header-ai-operator-count');
    if (aiOperatorCountEl) {
      aiOperatorCountEl.textContent = data.ai_operator_count || 45;
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
  }

  updateHeaderHeight() {
    const header = document.querySelector('.app-header') || (document.getElementById('app-header')?.querySelector('.app-header'));
    if (!header) return;
    
    const height = header.offsetHeight;
    const gap = 16;
    const offset = height + gap;
    
    document.documentElement.style.setProperty('--app-header-h', height + 'px');
    document.documentElement.style.setProperty('--app-header-offset', offset + 'px');
  }

  initResizeObserver() {
    const header = document.querySelector('.app-header') || (document.getElementById('app-header')?.querySelector('.app-header'));
    if (!header || typeof ResizeObserver === 'undefined') return;
    
    const observer = new ResizeObserver(() => {
      this.updateHeaderHeight();
    });
    
    observer.observe(header);
    window.addEventListener('resize', () => this.updateHeaderHeight());
  }

  async handleLogout() {
    try {
      await fetch('/api/logout', { method: 'POST', credentials: 'same-origin' });
      location.reload();
    } catch (e) {
      console.error('Logout error:', e);
    }
  }

  async refreshUserBox() {
    await this.initUserBox();
  }
}

// Auto-init když je DOM ready
let appHeaderInstance = null;

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    appHeaderInstance = new AppHeader();
    window.appHeader = appHeaderInstance;
  });
} else {
  appHeaderInstance = new AppHeader();
  window.appHeader = appHeaderInstance;
}

// Exponovat refreshUserBox globálně
window.refreshUserBox = function() {
  if (appHeaderInstance) {
    appHeaderInstance.refreshUserBox();
  }
};

// Globální logout funkce
window.logout = function() {
  if (appHeaderInstance) {
    appHeaderInstance.handleLogout();
  } else {
    fetch('/api/logout', { method: 'POST', credentials: 'same-origin' })
      .then(() => location.reload())
      .catch(() => location.href = '/login.html');
  }
};

// Search modal
window.openSearchModal = function() {
    const modal = document.getElementById('search-modal');
    if (modal) {
        modal.classList.add('open');
    } else {
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
        window.location.href = '/notifications.html';
    }
};
