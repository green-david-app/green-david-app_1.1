// Automatické nastavení active stavu podle aktuální stránky
document.addEventListener('DOMContentLoaded', () => {
    const currentPage = window.location.pathname;
    const navItems = document.querySelectorAll('.bottom-nav .nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (!href) return;
        
        // Remove active from all
        item.classList.remove('active');
        
        // Add active to current page
        if (href === currentPage || 
            (currentPage === '/' && (href === '/index.html' || href === '/')) ||
            (currentPage.includes('index') && (href === '/index.html' || href === '/')) ||
            (currentPage.includes('jobs') && href.includes('jobs')) ||
            (currentPage.includes('timesheets') && href.includes('timesheets')) ||
            (currentPage.includes('calendar') && href.includes('calendar')) ||
            (currentPage.includes('tasks') && href.includes('tasks')) ||
            (currentPage.includes('settings') && href.includes('settings'))) {
            item.classList.add('active');
        }
    });
});

