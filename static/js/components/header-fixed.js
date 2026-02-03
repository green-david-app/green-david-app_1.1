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
        
        <!-- 5. ÚKOLY - pouze ikona s badge -->
        <a href="/tasks" class="header-tasks" title="Úkoly">
            <svg viewBox="0 0 24 24" width="22" height="22">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" fill="currentColor"/>
            </svg>
            ${tasksCount > 0 ? `<span class="header-badge" id="header-tasks-badge">${tasksCount}</span>` : ''}
        </a>
        
        <!-- 6. NOTIFIKACE - větší zvonek -->
        <button class="header-notifications" onclick="toggleNotificationsDropdown()" title="Notifikace">
            <svg viewBox="0 0 24 24" width="24" height="24">
                <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2zm-2 1H8v-6c0-2.48 1.51-4.5 4-4.5s4 2.02 4 4.5v6z" fill="currentColor"/>
            </svg>
            ${notificationsCount > 0 ? `<span class="notification-badge" id="header-notif-badge">${notificationsCount}</span>` : ''}
        </button>
        
        <!-- 7. NASTAVENÍ - lepší ozubené kolečko -->
        <a href="/settings.html" class="header-settings" title="Nastavení">
            <svg viewBox="0 0 24 24" width="24" height="24">
                <path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.09-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.09.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z" fill="currentColor"/>
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
    // Aktualizovat tasks badge
    const tasksBadge = document.getElementById('header-tasks-badge');
    if (tasksBadge) {
      if (data.tasks_count > 0) {
        tasksBadge.textContent = data.tasks_count;
        tasksBadge.style.display = 'flex';
      } else {
        tasksBadge.style.display = 'none';
      }
    } else if (data.tasks_count > 0) {
      // Vytvořit badge pokud neexistuje
      const tasksLink = document.querySelector('.header-tasks');
      if (tasksLink && !tasksLink.querySelector('.header-badge')) {
        const badge = document.createElement('span');
        badge.className = 'header-badge';
        badge.id = 'header-tasks-badge';
        badge.textContent = data.tasks_count;
        tasksLink.appendChild(badge);
      }
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
