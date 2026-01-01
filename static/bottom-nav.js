// Univerzální bottom navigation pro celou aplikaci
function createBottomNav() {
    const currentPath = window.location.pathname;
    const currentSearch = window.location.search;
    
    const navItems = [
        {
            href: '/',
            icon: `<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>`,
            label: 'Domů',
            paths: ['/index.html', '/', '/?tab=dashboard']
        },
        {
            href: '/jobs.html',
            icon: `<path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 12h6"/><path d="M9 16h6"/>`,
            label: 'Zakázky',
            paths: ['/jobs.html', '/?tab=jobs']
        },
        {
            href: '/timesheets.html',
            icon: `<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>`,
            label: 'Výkazy',
            paths: ['/timesheets.html']
        },
        {
            href: '/calendar.html',
            icon: `<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>`,
            label: 'Kalendář',
            paths: ['/calendar.html']
        },
        {
            href: '#',
            icon: `<circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>`,
            label: 'Více',
            paths: [],
            isMoreMenu: true
        },
        {
            href: '/settings.html',
            icon: `<circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"/>`,
            label: 'Nastavení',
            paths: ['/settings.html']
        }
    ];
    
    const nav = document.createElement('nav');
    nav.className = 'bottom-nav';
    
    nav.innerHTML = navItems.map(item => {
        const isActive = item.paths.some(path => 
            currentPath === path || 
            currentPath.includes(path.replace('/', '')) ||
            (currentSearch && currentSearch.includes(path.replace('/', '')))
        );
        
        const onclickAttr = item.isMoreMenu ? `onclick="event.preventDefault(); const menu = document.getElementById('more-menu'); if (menu) menu.classList.toggle('show');"` : '';
        
        return `
            <a href="${item.href}" class="nav-item ${isActive ? 'active' : ''}" ${onclickAttr}>
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
document.addEventListener('DOMContentLoaded', () => {
    // Najdi existující bottom nav a nahraď ji
    const existingNav = document.querySelector('.bottom-nav');
    if (existingNav) {
        existingNav.remove();
    }
    
    // Vytvoř novou navigation
    const nav = createBottomNav();
    document.body.appendChild(nav);
});
