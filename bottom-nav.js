// Univerzální bottom navigation pro celou aplikaci
function createBottomNav() {
    const currentPath = window.location.pathname;
    const currentSearch = window.location.search;

// I18N helper (falls back to original Czech if unavailable)
function navLabel(key, fallback) {
    try {
        if (window.AppI18n && typeof window.AppI18n.t === 'function') {
            const v = window.AppI18n.t(key);
            return v || fallback;
        }
    } catch (_) {}
    return fallback;
}
    
    const navItems = [
        {
            href: '/',
            icon: `<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>`,
            labelKey: 'nav.home',
            label: 'Domů',
            paths: ['/index.html', '/', '/?tab=dashboard']
        },
        {
            href: '/jobs.html',
            icon: `<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 12h6"/><path d="M9 16h6"/>`,
            labelKey: 'nav.jobs',
            label: 'Zakázky',
            paths: ['/jobs.html', '/?tab=jobs']
        },
        {
            href: '/timesheets.html',
            icon: `<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>`,
            labelKey: 'nav.timesheets',
            label: 'Výkazy',
            paths: ['/timesheets.html', '/templates/timesheets.html']
        },
        {
            href: '/calendar.html',
            icon: `<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>`,
            labelKey: 'nav.calendar',
            label: 'Kalendář',
            paths: ['/calendar.html']
        },
        {
            href: '/reports.html',
            icon: `<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>`,
            labelKey: 'nav.reports',
            label: 'Přehledy',
            paths: ['/reports.html', '/?tab=reports']
        },
        {
            href: '#',
            icon: `<circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>`,
            labelKey: 'nav.more',
            label: 'Více',
            paths: [],
            isMoreMenu: true
        }
    ];
    
    const nav = document.createElement('nav');
    nav.className = 'bottom-nav';
    
    nav.innerHTML = navItems.map(item => {
        const label = navLabel(item.labelKey, item.label);

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
            <a href="${item.href}" class="nav-item ${isActive ? 'active' : ''}" ${onclickAttr} data-nav-item="${item.labelKey || item.label}">
                <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    ${item.icon}
                </svg>
                <span>${item.labelKey ? navLabel(item.labelKey, item.label) : item.label}</span>
            </a>
        `;
    }).join('');
    
    return nav;
}

// Inicializuj bottom nav při načtení stránky
function initBottomNav() {
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
    // Pokud už existuje, nemaž ho
    if (document.getElementById('more-menu')) return;

    const menu = document.createElement('div');
    menu.id = 'more-menu';
    menu.className = 'more-menu';

    // I18N helper
    const tt = (key, fallback) => {
        try {
            if (window.AppI18n && typeof window.AppI18n.t === 'function') {
                const v = window.AppI18n.t(key);
                return v || fallback;
            }
        } catch (_) {}
        return fallback;
    };

    menu.innerHTML = `
        <div class="more-menu-panel">
            <div class="more-menu-header">
                <div style="font-size:18px;font-weight:600;color:#e8eef2;">${tt('more.title','Navigace')}</div>
                <button onclick="toggleMoreMenu()" style="background:none;border:none;color:#9ca8b3;cursor:pointer;font-size:24px;line-height:1;width:32px;height:32px;display:flex;align-items:center;justify-content:center;">×</button>
            </div>
            <div class="more-menu-content">
                <a href="/" class="more-menu-item"><span>${tt('more.dashboard','přehled')}</span></a>
                <a href="/inbox.html" class="more-menu-item"><span>${tt('more.inbox','moje práce')}</span></a>
                <a href="/calendar.html" class="more-menu-item"><span>${tt('more.calendar','kalendář')}</span></a>
                <a href="/timesheets.html" class="more-menu-item"><span>${tt('more.timesheets','výkazy hodin')}</span></a>
                <a href="/jobs.html" class="more-menu-item"><span>${tt('more.jobs','zakázky')}</span></a>
                <a href="/tasks.html" class="more-menu-item"><span>${tt('more.tasks','úkoly')}</span></a>
                <a href="/employees.html" class="more-menu-item"><span>${tt('more.employees','team')}</span></a>
                <a href="/warehouse.html" class="more-menu-item"><span>${tt('more.warehouse','sklad')}</span></a>
                <a href="/finance.html" class="more-menu-item"><span>${tt('more.finance','finance')}</span></a>
                <a href="/documents.html" class="more-menu-item"><span>${tt('more.documents','dokumenty')}</span></a>
                <a href="/reports.html" class="more-menu-item"><span>${tt('more.reports','reporty')}</span></a>
                <a href="/archive.html" class="more-menu-item"><span>${tt('more.archive','archiv')}</span></a>
                <a href="/settings.html" class="more-menu-item"><span>${tt('more.settings','nastavení')}</span></a>
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
    
    const isShowing = menu.classList.toggle('show');
    
    // Dynamicky skryj/zobraz bottom-nav
    const bottomNav = document.querySelector('.bottom-nav');
    const bottomNavContainer = document.getElementById('bottom-nav-container');
    
    if (isShowing) {
        // Skryj bottom toolbar
        if (bottomNav) {
            bottomNav.style.display = 'none';
            bottomNav.style.opacity = '0';
            bottomNav.style.visibility = 'hidden';
            bottomNav.style.pointerEvents = 'none';
        }
        if (bottomNavContainer) {
            bottomNavContainer.style.display = 'none';
            bottomNavContainer.style.opacity = '0';
            bottomNavContainer.style.visibility = 'hidden';
        }
        
        // Přidej event listenery na všechny odkazy v menu pro automatické zavření
        const menuLinks = menu.querySelectorAll('.more-menu-item');
        menuLinks.forEach(link => {
            link.addEventListener('click', () => {
                menu.classList.remove('show');
                // Obnov bottom toolbar
                if (bottomNav) {
                    bottomNav.style.display = '';
                    bottomNav.style.opacity = '';
                    bottomNav.style.visibility = '';
                    bottomNav.style.pointerEvents = '';
                }
                if (bottomNavContainer) {
                    bottomNavContainer.style.display = '';
                    bottomNavContainer.style.opacity = '';
                    bottomNavContainer.style.visibility = '';
                }
            }, { once: true });
        });
    } else {
        // Obnov bottom toolbar
        if (bottomNav) {
            bottomNav.style.display = '';
            bottomNav.style.opacity = '';
            bottomNav.style.visibility = '';
            bottomNav.style.pointerEvents = '';
        }
        if (bottomNavContainer) {
            bottomNavContainer.style.display = '';
            bottomNavContainer.style.opacity = '';
            bottomNavContainer.style.visibility = '';
        }
    }
}

// Zavři menu při kliknutí mimo něj nebo na backdrop
document.addEventListener('click', (e) => {
    const menu = document.getElementById('more-menu');
    const moreButton = document.querySelector('.nav-item[onclick*="toggleMoreMenu"]');
    const menuPanel = menu?.querySelector('.more-menu-panel');
    
    if (menu && menu.classList.contains('show')) {
        // Zavři pokud kliknutí je MIMO panel a MIMO tlačítko "Více"
        // NEBO pokud kliknutí je přímo na backdrop (more-menu, ale ne panel)
        if ((!menuPanel?.contains(e.target) && !moreButton?.contains(e.target)) ||
            (e.target === menu)) {
            menu.classList.remove('show');
            
            // Obnov bottom toolbar
            const bottomNav = document.querySelector('.bottom-nav');
            const bottomNavContainer = document.getElementById('bottom-nav-container');
            if (bottomNav) {
                bottomNav.style.display = '';
                bottomNav.style.opacity = '';
                bottomNav.style.visibility = '';
                bottomNav.style.pointerEvents = '';
            }
            if (bottomNavContainer) {
                bottomNavContainer.style.display = '';
                bottomNavContainer.style.opacity = '';
                bottomNavContainer.style.visibility = '';
            }
        }
    }
});
