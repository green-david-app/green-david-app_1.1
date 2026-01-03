// Unified Header Component
class AppHeader {
  constructor() {
    this.render();
    this.initUserBox();
  }

  render() {
    // Zkontrolovat, zda už header neexistuje
    const existingHeader = document.querySelector('.app-header');
    if (existingHeader) {
      // Header už existuje, pouze zajistit že má správnou strukturu
      this.ensureHeaderStructure(existingHeader);
      return;
    }

    const headerHTML = `
      <header class="app-header">
        <div class="app-header-container">
          <a href="/" class="app-header-brand">
            <img src="/logo.jpg" alt="green david app" class="app-header-logo" onerror="this.src='/logo.svg'"/>
            <div class="app-header-text">
              <div class="app-header-title">green david app</div>
              <div class="app-header-subtitle">interní systém</div>
            </div>
          </a>
          <div class="app-header-actions">
            <div id="userbox" class="app-header-user"></div>
            <a href="/settings.html" class="app-header-settings" title="Nastavení">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"/>
              </svg>
            </a>
          </div>
        </div>
      </header>
    `;

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
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"/>
          <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"/>
        </svg>
      `;
      actions.appendChild(settingsLink);
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
        box.innerHTML = `
          <span>Úkoly: <strong style="color:#e8eef2;">${j.tasks_count || 0}</strong></span>
          <button class="btn btn-ghost btn-sm" id="logout-btn" style="padding:6px 12px;font-size:13px;">Odhlásit</button>
        `;
        
        // Přidat event listener pro logout tlačítko
        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
          logoutBtn.addEventListener('click', () => this.handleLogout());
        }
      } else {
        box.innerHTML = '<span style="color:#9ca8b3;">Nepřihlášen</span>';
      }
    } catch (e) {
      console.error('UserBox error:', e);
      box.innerHTML = '';
    }
  }

  // Metoda pro refresh userboxu (může být volána zvenčí)
  async refreshUserBox() {
    await this.initUserBox();
  }

  async handleLogout() {
    try {
      await fetch('/api/logout', { method: 'POST', credentials: 'same-origin' });
      location.reload();
    } catch (e) {
      console.error('Logout error:', e);
    }
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

