// Univerzální bottom navigation pro celou aplikaci
function createBottomNav() {
    // Na desktopu se sidebarem - neiniciuj bottom nav
    if (window.innerWidth > 768 && document.querySelector('.app-sidebar')) {
        // Smaž existující bottom nav pokud existuje
        const existingNav = document.querySelector('.bottom-nav');
        if (existingNav) existingNav.remove();
        const container = document.getElementById('bottom-nav-container');
        if (container) container.style.display = 'none';
        return;
    }
    
    const t = (k) => (window.AppI18n && typeof window.AppI18n.t === 'function') ? window.AppI18n.t(k) : k;
    const currentPath = window.location.pathname;
    const currentSearch = window.location.search;
    
    const navItems = [
        {
            href: '/',
            icon: `<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>`,
            label: t('nav.home'),
            paths: ['/index.html', '/', '/?tab=dashboard']
        },
        {
            href: '/jobs.html',
            icon: `<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 12h6"/><path d="M9 16h6"/>`,
            label: t('nav.jobs'),
            paths: ['/jobs.html', '/?tab=jobs']
        },
        {
            href: '/timesheets.html',
            icon: `<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>`,
            label: t('nav.timesheets'),
            paths: ['/timesheets.html', '/templates/timesheets.html']
        },
        {
            href: '/calendar.html',
            icon: `<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>`,
            label: t('nav.calendar'),
            paths: ['/calendar.html']
        },
        {
            href: '/reports.html',
            icon: `<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>`,
            label: t('nav.reports'),
            paths: ['/reports.html', '/?tab=reports']
        },
        {
            href: '#',
            icon: `<circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>`,
            label: t('nav.more'),
            paths: [],
            isMoreMenu: true
        }
    ];
    
    const nav = document.createElement('nav');
    nav.className = 'bottom-nav';
    
    nav.innerHTML = navItems.map(item => {
        // Lepší detekce aktivní stránky
        let isActive = false;
        if (item.paths.length > 0) {
            isActive = item.paths.some(path => {
                // Přesná shoda cesty
                if (currentPath === path) return true;
                // Shoda s query parametrem
                if (path.startsWith('/?') && currentSearch) {
                    const pathParams = new URLSearchParams(path.substring(2));
                    const currentParams = new URLSearchParams(currentSearch.substring(1));
                    for (const [key, value] of pathParams.entries()) {
                        if (currentParams.get(key) === value) return true;
                    }
                }
                // Pro standalone stránky - přesná shoda nebo začátek cesty
                if (path.startsWith('/') && !path.startsWith('/?')) {
                    if (currentPath === path || currentPath.startsWith(path + '/')) return true;
                }
                return false;
            });
        }
        
        // Pro "Více" menu použijeme onclick, pro ostatní použijeme event listenery
        const onclickAttr = item.isMoreMenu ? `onclick="event.preventDefault(); toggleMoreMenu();"` : '';
        
        return `
            <a href="${item.href}" class="nav-item ${isActive ? 'active' : ''}" ${onclickAttr} data-nav-item="${item.label}">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    ${item.icon}
                </svg>
                <span>${item.label}</span>
            </a>
        `;
    }).join('');
    
    return nav;
}

// Inicializuj bottom nav při načtení stránky
function initBottomNav() {
    // Sidebar nahrazuje bottom nav na desktopu
    if (document.querySelector('.app-sidebar')) {
        return;
    }
    // Desktop se sidebarem — neinicializuj bottom nav
    if (document.querySelector('.app-sidebar') || document.body.classList.contains('has-sidebar')) {
        const existingNav = document.querySelector('.bottom-nav');
        if (existingNav) existingNav.remove();
        const container = document.getElementById('bottom-nav-container');
        if (container) container.innerHTML = '';
        return;
    }
    // Najdi existující bottom nav a nahraď ji
    const existingNav = document.querySelector('.bottom-nav');
    if (existingNav) {
        existingNav.remove();
    }
    
    // Zkontroluj, jestli existuje container
    let container = document.getElementById('bottom-nav-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'bottom-nav-container';
        document.body.appendChild(container);
    }
    
    // Vytvoř novou navigation
    const nav = createBottomNav();
    container.appendChild(nav);
    
    // Vytvoř "Více" menu pokud ještě neexistuje
    createMoreMenu();
    
    // Přidat event listenery na všechny odkazy
    const navLinks = nav.querySelectorAll('.nav-item');
    navLinks.forEach(link => {
        // Přeskočit "Více" menu - má vlastní handler
        if (link.getAttribute('href') === '#') {
            return;
        }
        
        // Odstranit existující listenery (pokud existují)
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);
        
        newLink.addEventListener('click', (e) => {
            // Zajistit, že kliknutí není blokováno
            e.stopPropagation();
            
            const href = newLink.getAttribute('href');
            
            // Pro SPA aplikace (index.html s taby)
            if (href === '/' && typeof window.setAppTab === 'function') {
                e.preventDefault();
                e.stopImmediatePropagation();
                window.setAppTab('dashboard');
                window.history.pushState({}, '', '/');
                return false;
            }
            
            // Pro query parametry (?tab=jobs)
            if (href.startsWith('/?tab=')) {
                e.preventDefault();
                e.stopImmediatePropagation();
                const tab = href.split('tab=')[1].split('&')[0];
                if (typeof window.setAppTab === 'function') {
                    window.setAppTab(tab);
                }
                window.history.pushState({}, '', href);
                return false;
            }
            
            // Pro standalone stránky
            if (href.startsWith('/') && !href.startsWith('/?')) {
                // Pokud jsme na stejné stránce, jen scroll na top
                if (window.location.pathname === href) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    return false;
                }
                // Jinak normální navigace - necháme defaultní chování
                // Ale zajistíme, že se stránka načte
                return true;
            }
            
            return true;
        }, true); // Use capture phase to ensure we catch the event first
    });
    
    // Inicializuj Lucide ikony
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
}

// Zkus inicializovat okamžitě (pro případy, kdy je DOM už připravený)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initBottomNav);
} else {
    // DOM je už připravený
    initBottomNav();
}

// Také zkus po malém zpoždění (pro Flask templates a dynamické načítání)
setTimeout(initBottomNav, 100);

// Re-inicializuj při změně stránky (pro SPA navigaci)
window.addEventListener('popstate', () => {
    setTimeout(initBottomNav, 50);
});

// Re-inicializuj při změně hash (pro deep linking)
window.addEventListener('hashchange', () => {
    setTimeout(initBottomNav, 50);
});

// Zajistit, že bottom nav je vždy klikatelný a není blokován jinými event handlery
document.addEventListener('click', (e) => {
    // Pokud kliknutí je na bottom nav, zajistit že není blokováno
    if (e.target.closest('.bottom-nav') || e.target.closest('#bottom-nav-container')) {
        const navItem = e.target.closest('.nav-item');
        if (navItem && navItem.getAttribute('href') !== '#') {
            // Nechat event listenery v bottom-nav.js zpracovat kliknutí
            // Tento handler zajistí, že jiné handlery nebudou blokovat
            return;
        }
    }
}, true); // Use capture phase

// Vytvoř dropdown menu pro "Více"
function createMoreMenu() {
    if (document.querySelector('.app-sidebar')) return;
    // Na desktopu se sidebarem - netvořit more menu
    if (window.innerWidth > 768 && document.querySelector('.app-sidebar')) {
        return;
    }
    
    // Pokud už existuje, nemaž ho
    if (document.getElementById('more-menu')) return;
    
    const menu = document.createElement('div');
    menu.id = 'more-menu';
    menu.className = 'more-menu';
    menu.innerHTML = `
        <div class="more-menu-backdrop" onclick="toggleMoreMenu()"></div>
        <div class="more-menu-panel">
            <div class="more-menu-header">
                <div style="font-size:18px;font-weight:600;color:var(--text-primary);">Navigace</div>
                <button onclick="toggleMoreMenu()" style="background:none;border:none;color:var(--text-tertiary);cursor:pointer;font-size:24px;line-height:1;width:32px;height:32px;display:flex;align-items:center;justify-content:center;">×</button>
            </div>
            <div class="more-menu-content">
                <a href="/" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                    <span>Přehled</span>
                </a>
                <a href="/calendar.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    <span>Kalendář</span>
                </a>
                <a href="/timesheets.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    <span>Výkazy hodin</span>
                </a>
                <a href="/trainings.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                    <span>Školení</span>
                </a>
                <a href="/jobs.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
                    <span>Zakázky</span>
                </a>
                <a href="/tasks.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
                    <span>Úkoly</span>
                </a>
                <a href="/team" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    <span>Tým</span>
                </a>
                <a href="/warehouse.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>
                    <span>Sklad</span>
                </a>
                <a href="/finance.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
                    <span>Finance</span>
                </a>
                <a href="/planning-daily.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                    <span>Plánování</span>
                </a>
                <a href="/timeline.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
                    <span>Timeline</span>
                </a>
                <a href="/nursery.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M12 2a9 9 0 0 0-9 9c0 3.6 3.4 6.2 4.7 7.5.5.5 1 .9 1.3 1.2V22h6v-2.3c.3-.3.8-.7 1.3-1.2C17.6 17.2 21 14.6 21 11a9 9 0 0 0-9-9z"/><circle cx="12" cy="11" r="3"/></svg>
                    <span>Školka</span>
                </a>
                <a href="/ai-operator.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><path d="M21 12a9 9 0 1 1-9-9"/><path d="M21 3v9h-9"/></svg>
                    <span>AI Operátor</span>
                </a>
                <a href="/reports.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
                    <span>Reporty</span>
                </a>
                <a href="/settings.html" class="more-menu-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="20" height="20"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                    <span>Nastavení</span>
                </a>
            </div>
        </div>
    `;
    
    document.body.appendChild(menu);
}

// Toggle funkce pro more menu
function toggleMoreMenu() {
    const menu = document.getElementById('more-menu');
    if (!menu) {
        createMoreMenu();
        setTimeout(() => toggleMoreMenu(), 10);
        return;
    }
    const isShowing = menu.classList.contains('show');
    menu.classList.toggle('show');
    
    // Skrýt/zobrazit bottom-nav při otevření/zavření menu
    const bottomNav = document.querySelector('.bottom-nav');
    const bottomNavContainer = document.getElementById('bottom-nav-container');
    
    if (menu.classList.contains('show')) {
        // Menu se otevírá - skrýt bottom-nav
        if (bottomNav) bottomNav.style.display = 'none';
        if (bottomNavContainer) bottomNavContainer.style.display = 'none';
        document.body.classList.add('more-menu-open');
    } else {
        // Menu se zavírá - zobrazit bottom-nav
        if (bottomNav) bottomNav.style.display = '';
        if (bottomNavContainer) bottomNavContainer.style.display = '';
        document.body.classList.remove('more-menu-open');
    }
}

// Zavři menu při kliknutí mimo něj
document.addEventListener('click', (e) => {
    const menu = document.getElementById('more-menu');
    const moreButton = document.querySelector('.nav-item[onclick*="toggleMoreMenu"]');
    const menuPanel = menu?.querySelector('.more-menu-panel');
    
    if (menu && menu.classList.contains('show')) {
        // Zavři pokud kliknutí je MIMO panel a MIMO tlačítko "Více"
        if (!menuPanel?.contains(e.target) && !moreButton?.contains(e.target)) {
            menu.classList.remove('show');
        }
    }
});
