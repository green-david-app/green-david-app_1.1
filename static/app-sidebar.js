/**
 * APP SIDEBAR NAVIGATION
 * Wrapper přístup - obalí veškerý obsah body do wrapperu
 * Toto funguje na VŠECH stránkách bez ohledu na jejich layout
 */

(function() {
  'use strict';

  // 1. Vytvoř sidebar element
  const sidebar = document.createElement('div');
  sidebar.className = 'app-sidebar';
  sidebar.innerHTML = `
    <div class="sidebar-brand">
      <img src="/static/logo.svg" alt="Logo" class="sidebar-logo" 
           onerror="this.style.display='none'"/>
      <span class="sidebar-brand-text">green david</span>
      <button class="sidebar-close" id="sidebar-close-btn" aria-label="Zavřít sidebar">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    </div>
    <nav class="sidebar-nav">
      <a href="/" class="sidebar-item" data-paths="/, /index.html" data-roles="owner,manager,lander,worker">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>Přehled</span>
      </a>

      <div class="sidebar-section-label" data-roles="owner,manager,lander">OPERATIVA</div>
      <a href="/planning-daily.html" class="sidebar-item" data-paths="/planning-daily.html, /planning-week.html, /planning-costs.html, /planning-timeline.html" data-roles="owner,manager,lander">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>Mission Control</span>
      </a>
      <a href="/ai-operator.html" class="sidebar-item" data-paths="/ai-operator.html, /ai-operator" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><circle cx="12" cy="12" r="3"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
        <span>AI Asistent</span>
      </a>
      <a href="/timesheets.html" class="sidebar-item" data-paths="/timesheets.html, /timesheets" data-roles="owner,manager,lander,worker">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        <span>Výkazy</span>
      </a>

      <div class="sidebar-section-label" data-roles="owner,manager,lander,worker">PROJEKTY</div>
      <a href="/directory" class="sidebar-item" data-paths="/directory, /directory.html" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
        <span>Adresář</span>
      </a>
      <a href="/jobs.html" class="sidebar-item" data-paths="/jobs.html, /jobs" data-roles="owner,manager,lander">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
        <span>Zakázky</span>
      </a>
      <a href="/tasks.html" class="sidebar-item" data-paths="/tasks.html, /tasks" data-roles="owner,manager,lander,worker">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
        <span>Úkoly</span>
      </a>
      <a href="/calendar.html" class="sidebar-item" data-paths="/calendar.html, /calendar" data-roles="owner,manager,lander,worker">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        <span>Kalendář</span>
      </a>
      <a href="/planning/timeline" class="sidebar-item" data-paths="/planning/timeline, /planning-timeline.html" data-roles="owner,manager,lander">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        <span>Timeline</span>
      </a>

      <div class="sidebar-section-label" data-roles="owner,manager">LIDÉ</div>
      <a href="/team.html" class="sidebar-item" data-paths="/team.html, /team, /employees.html, /employee-detail.html" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
        <span>Tým</span>
      </a>
      <a href="/trainings.html" class="sidebar-item" data-paths="/trainings.html, /trainings" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
        <span>Školení</span>
      </a>

      <div class="sidebar-section-label" data-roles="owner,manager,lander">ZÁSOBOVÁNÍ</div>
      <a href="/warehouse.html" class="sidebar-item" data-paths="/warehouse.html, /materials.html" data-roles="owner,manager,lander">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
        <span>Sklad</span>
      </a>
      <a href="/nursery.html" class="sidebar-item" data-paths="/nursery.html, /plant-database.html" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M7 20h10M12 20V10"/><path d="M12 10C12 6 7 3.5 4 5.5c3 0 5.5 1 8 4.5z"/><path d="M12 10c0-4 5-6.5 8-4.5-3 0-5.5 1-8 4.5z"/></svg>
        <span>Školka</span>
      </a>

      <div class="sidebar-section-label" data-roles="owner,manager">NÁSTROJE</div>
      <a href="/reports.html" class="sidebar-item" data-paths="/reports.html, /reports-hub.html, /reports-daily.html, /reports-week.html, /reports-project.html" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        <span>Reporty</span>
      </a>
      <a href="/finance.html" class="sidebar-item" data-paths="/finance.html" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
        <span>Finance</span>
      </a>
      <a href="/documents.html" class="sidebar-item" data-paths="/documents.html" data-roles="owner,manager">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
        <span>Dokumenty</span>
      </a>
      <a href="/notes.html" class="sidebar-item" data-paths="/notes.html, /notes" data-roles="owner,manager,lander">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg>
        <span>Poznámky</span>
      </a>
      <a href="/settings.html" class="sidebar-item" data-paths="/settings.html, /settings" data-roles="owner">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        <span>Nastavení</span>
      </a>
    </nav>
    <div class="sidebar-footer">
      <div class="sidebar-user">
        <div class="sidebar-avatar">A</div>
        <div class="sidebar-user-info">
          <div class="sidebar-user-name">Admin</div>
          <div class="sidebar-user-role">Owner</div>
        </div>
      </div>
      <a href="/logout" class="sidebar-item sidebar-logout">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
        <span>Odhlásit se</span>
      </a>
    </div>
  `;

  // 2. KLÍČOVÝ KROK: Obal veškerý obsah body do wrapperu
  const wrapper = document.createElement('div');
  wrapper.className = 'sidebar-content-wrapper';
  
  // Přesuň VŠECHNY existující children z body do wrapperu
  // KROMĚ sidebaru a app-header (ten musí zůstat přímý child body pro position:fixed)
  const existingSidebar = document.querySelector('.app-sidebar');
  if (existingSidebar) {
    existingSidebar.remove();
  }
  
  // Zapamatuj si header element, abychom ho po obalení vrátili zpět do body
  const appHeader = document.querySelector('header.app-header');
  if (appHeader) {
    appHeader.remove();
  }
  
  while (document.body.firstChild) {
    wrapper.appendChild(document.body.firstChild);
  }
  
  // Vlož sidebar a wrapper zpět do body
  document.body.appendChild(sidebar);
  document.body.appendChild(wrapper);
  
  // Header ZPĚT jako přímý child body (PŘED wrapper) pro position:fixed
  if (appHeader) {
    document.body.insertBefore(appHeader, wrapper);
  }
  
  document.body.classList.add('has-sidebar');

  // 3. SIDEBAR TOGGLE — slide in/out s uložením stavu
  function hideSidebar() {
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebar) {
      sidebar.classList.remove('open', 'active', 'visible', 'sidebar-open');
    }
    document.body.classList.remove('sidebar-open');
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) overlay.classList.remove('active');
    
    // Desktop: použij starý systém
    if (window.innerWidth > 768) {
      document.body.classList.add('sidebar-hidden');
      try { localStorage.setItem('gd-sidebar-hidden', '1'); } catch(e) {}
    }
  }
  
  function showSidebar() {
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebar) {
      sidebar.classList.add('open');
    }
    document.body.classList.add('sidebar-open');
    
    // Vytvoř overlay pokud neexistuje (mobil)
    if (window.innerWidth <= 768) {
      let overlay = document.querySelector('.sidebar-overlay');
      if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.onclick = () => hideSidebar();
        document.body.appendChild(overlay);
      }
      overlay.classList.add('active');
    }
    
    // Desktop: použij starý systém
    if (window.innerWidth > 768) {
      document.body.classList.remove('sidebar-hidden');
      try { localStorage.setItem('gd-sidebar-hidden', '0'); } catch(e) {}
    }
  }
  
  function toggleSidebar() {
    const sidebar = document.querySelector('.app-sidebar');
    const isOpen = sidebar && sidebar.classList.contains('open');
    
    if (isOpen) {
      hideSidebar();
    } else {
      showSidebar();
    }
  }

  // X button = skrýt sidebar
  const closeBtn = document.getElementById('sidebar-close-btn');
  if (closeBtn) {
    closeBtn.addEventListener('click', hideSidebar);
  }

  // Expose pro header hamburger (☰)
  window.appSidebar = { toggle: toggleSidebar, show: showSidebar, hide: hideSidebar };

  // Na mobilu: sidebar VŽDY zavřený při startu
  if (window.innerWidth <= 768) {
    hideSidebar();
  } else {
    // Desktop: obnov uložený stav
    try {
      if (localStorage.getItem('gd-sidebar-hidden') === '1') {
        document.body.classList.add('sidebar-hidden');
      }
    } catch(e) {}
  }

  // 4. Zvýrazni aktivní stránku
  const currentPath = window.location.pathname;
  sidebar.querySelectorAll('.sidebar-item').forEach(item => {
    const paths = (item.getAttribute('data-paths') || '').split(',').map(p => p.trim());
    if (paths.some(p => {
      if (p === '/' && (currentPath === '/' || currentPath === '/index.html')) return true;
      if (p !== '/' && (currentPath === p || currentPath.startsWith(p + '/'))) return true;
      return false;
    })) {
      item.classList.add('active');
    }
  });

  // 4. Skryj bottom nav na desktopu (je nahrazený sidebarem)
  const bottomNav = document.querySelector('.bottom-nav');
  if (bottomNav) bottomNav.style.display = 'none';
  const bottomNavContainer = document.getElementById('bottom-nav-container');
  if (bottomNavContainer) bottomNavContainer.style.display = 'none';
  const moreMenu = document.getElementById('more-menu');
  if (moreMenu) moreMenu.style.display = 'none';

  // 5. Uprav header pokud existuje
  const header = wrapper.querySelector('.app-header');
  if (header) {
    // Header už je v wrapperu, CSS ho upraví automaticky
  }

  // 6. Role-based access control (RBAC)
  async function applySidebarRoles() {
    try {
      const res = await fetch('/api/me');
      const data = await res.json();
      
      // Normalizace role - admin → owner
      let userRole = (data.role || data.user?.role || 'worker').toLowerCase();
      if (userRole === 'admin') {
        userRole = 'owner';
      }
      
      // Ulož roli globálně pro použití na stránkách
      window.GD_USER_ROLE = userRole;
      
      // Skryj sidebar položky které uživatel nemá vidět
      document.querySelectorAll('[data-roles]').forEach(el => {
        const allowedRoles = el.getAttribute('data-roles').split(',').map(r => r.trim());
        if (!allowedRoles.includes(userRole)) {
          el.style.display = 'none';
        }
      });
      
      // Skryj section labels pokud všechny jejich děti jsou skryté
      document.querySelectorAll('.sidebar-section-label[data-roles]').forEach(label => {
        const labelRoles = label.getAttribute('data-roles').split(',').map(r => r.trim());
        if (!labelRoles.includes(userRole)) {
          label.style.display = 'none';
        } else {
          // Zkontroluj jestli má nějaké viditelné děti
          let hasVisibleChildren = false;
          let nextEl = label.nextElementSibling;
          while (nextEl && !nextEl.classList.contains('sidebar-section-label')) {
            if (nextEl.classList.contains('sidebar-item') && nextEl.style.display !== 'none') {
              hasVisibleChildren = true;
              break;
            }
            nextEl = nextEl.nextElementSibling;
          }
          if (!hasVisibleChildren) {
            label.style.display = 'none';
          }
        }
      });
      
      // Aktualizuj jméno a roli v sidebar footer
      const roleLabels = { owner: 'Majitel', manager: 'Manažer', lander: 'Parťák', worker: 'Pracovník' };
      const nameEl = document.querySelector('.sidebar-user-name');
      const roleEl = document.querySelector('.sidebar-user-role');
      if (nameEl && data.name) nameEl.textContent = data.name;
      if (roleEl) roleEl.textContent = roleLabels[userRole] || userRole;
      
      // Avatar - první písmeno jména
      const avatarEl = document.querySelector('.sidebar-avatar');
      if (avatarEl && data.name) avatarEl.textContent = data.name.charAt(0).toUpperCase();
      
      // Ochrana stránek — redirect pokud uživatel nemá přístup
      const pageRoleMap = {
        '/planning-daily.html': ['owner','manager','lander'],
        '/planning-week.html': ['owner','manager','lander'],
        '/planning-costs.html': ['owner','manager'],
        '/ai-operator.html': ['owner','manager'],
        '/directory': ['owner','manager'],
        '/directory.html': ['owner','manager'],
        '/jobs.html': ['owner','manager','lander'],
        '/team.html': ['owner','manager'],
        '/trainings.html': ['owner','manager'],
        '/warehouse.html': ['owner','manager','lander'],
        '/nursery.html': ['owner','manager'],
        '/reports.html': ['owner','manager'],
        '/reports-hub.html': ['owner','manager'],
        '/reports-daily.html': ['owner','manager'],
        '/reports-week.html': ['owner','manager'],
        '/reports-project.html': ['owner','manager'],
        '/finance.html': ['owner','manager'],
        '/documents.html': ['owner','manager'],
        '/notes.html': ['owner','manager','lander'],
        '/notes': ['owner','manager','lander'],
        '/settings.html': ['owner'],
        '/planning-timeline.html': ['owner','manager','lander'],
        '/planning/timeline': ['owner','manager','lander']
      };
      
      const currentPath = window.location.pathname;
      const allowedForPage = pageRoleMap[currentPath];
      if (allowedForPage && !allowedForPage.includes(userRole)) {
        window.location.href = '/';
        return;
      }
    } catch (e) {
      console.warn('Sidebar role check failed:', e);
    }
  }

  // Zavolej po DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applySidebarRoles);
  } else {
    applySidebarRoles();
  }
})();
