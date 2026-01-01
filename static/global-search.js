// Global Search with Cmd/Ctrl+K shortcut
(function() {
    let searchOverlay = null;
    let searchInput = null;
    let resultsContainer = null;
    let currentResults = [];

    function createSearchOverlay() {
        if (searchOverlay) return;

        searchOverlay = document.createElement('div');
        searchOverlay.id = 'global-search-overlay';
        searchOverlay.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(8px);
            z-index: 10000;
            align-items: flex-start;
            justify-content: center;
            padding-top: 100px;
        `;

        const searchBox = document.createElement('div');
        searchBox.style.cssText = `
            background: #1a1a1a;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            animation: slideDown 0.2s ease;
        `;

        searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.placeholder = '🔍 Hledat zakázky, úkoly, zaměstnance...';
        searchInput.style.cssText = `
            width: 100%;
            padding: 20px 24px;
            background: transparent;
            border: none;
            color: #fff;
            font-size: 18px;
            outline: none;
        `;

        resultsContainer = document.createElement('div');
        resultsContainer.id = 'search-results';
        resultsContainer.style.cssText = `
            max-height: 400px;
            overflow-y: auto;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        `;

        const footer = document.createElement('div');
        footer.style.cssText = `
            padding: 12px 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
        `;
        footer.innerHTML = `
            <span>⌘K nebo Ctrl+K pro otevření</span>
            <span>Esc pro zavření</span>
        `;

        searchBox.appendChild(searchInput);
        searchBox.appendChild(resultsContainer);
        searchBox.appendChild(footer);
        searchOverlay.appendChild(searchBox);

        // Close on backdrop click
        searchOverlay.addEventListener('click', (e) => {
            if (e.target === searchOverlay) {
                closeSearch();
            }
        });

        // Close on Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && searchOverlay.style.display === 'flex') {
                closeSearch();
            }
        });

        // Search on input
        searchInput.addEventListener('input', (e) => {
            performSearch(e.target.value);
        });

        // Navigate results with arrow keys
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                const firstResult = resultsContainer.querySelector('.search-result-item');
                if (firstResult) firstResult.focus();
            }
        });

        document.body.appendChild(searchOverlay);
    }

    function openSearch() {
        createSearchOverlay();
        searchOverlay.style.display = 'flex';
        searchInput.focus();
        searchInput.value = '';
        resultsContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.5);">Začněte psát pro vyhledávání...</div>';
    }

    function closeSearch() {
        if (searchOverlay) {
            searchOverlay.style.display = 'none';
            searchInput.value = '';
        }
    }

    async function performSearch(query) {
        if (!query || query.length < 2) {
            resultsContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.5);">Zadejte alespoň 2 znaky</div>';
            return;
        }

        resultsContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.5);">🔍 Hledám...</div>';

        try {
            // Search in multiple APIs
            const [jobsRes, tasksRes, employeesRes] = await Promise.all([
                fetch('/api/jobs').catch(() => null),
                fetch('/api/tasks').catch(() => null),
                fetch('/api/employees').catch(() => null)
            ]);

            const results = [];

            // Jobs
            if (jobsRes && jobsRes.ok) {
                const jobs = await jobsRes.json();
                (jobs.jobs || []).forEach(job => {
                    const title = (job.title || '').toLowerCase();
                    const client = (job.client || '').toLowerCase();
                    const q = query.toLowerCase();
                    if (title.includes(q) || client.includes(q)) {
                        results.push({
                            type: 'zakázka',
                            icon: '📋',
                            title: job.title || `Zakázka ${job.id}`,
                            subtitle: job.client || '',
                            url: `/jobs.html#job-${job.id}`,
                            id: job.id
                        });
                    }
                });
            }

            // Tasks
            if (tasksRes && tasksRes.ok) {
                const tasks = await tasksRes.json();
                (tasks.tasks || []).forEach(task => {
                    const title = (task.title || '').toLowerCase();
                    const q = query.toLowerCase();
                    if (title.includes(q)) {
                        results.push({
                            type: 'úkol',
                            icon: '✅',
                            title: task.title || `Úkol ${task.id}`,
                            subtitle: task.status || '',
                            url: `/tasks.html#task-${task.id}`,
                            id: task.id
                        });
                    }
                });
            }

            // Employees
            if (employeesRes && employeesRes.ok) {
                const employees = await employeesRes.json();
                (employees.employees || []).forEach(emp => {
                    const name = (emp.name || '').toLowerCase();
                    const role = (emp.role || '').toLowerCase();
                    const q = query.toLowerCase();
                    if (name.includes(q) || role.includes(q)) {
                        results.push({
                            type: 'zaměstnanec',
                            icon: '👥',
                            title: emp.name || `Zaměstnanec ${emp.id}`,
                            subtitle: emp.role || '',
                            url: `/employees.html#emp-${emp.id}`,
                            id: emp.id
                        });
                    }
                });
            }

            renderResults(results);

        } catch (e) {
            console.error('Search error:', e);
            resultsContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: #f87171;">Chyba při vyhledávání</div>';
        }
    }

    function renderResults(results) {
        if (results.length === 0) {
            resultsContainer.innerHTML = '<div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.5);">Žádné výsledky</div>';
            return;
        }

        // Group by type
        const grouped = {};
        results.forEach(r => {
            if (!grouped[r.type]) grouped[r.type] = [];
            grouped[r.type].push(r);
        });

        let html = '';
        Object.keys(grouped).forEach(type => {
            html += `<div style="padding: 12px 24px; background: rgba(255,255,255,0.03); font-size: 11px; color: rgba(255,255,255,0.5); text-transform: uppercase; font-weight: 600;">${type}</div>`;
            grouped[type].slice(0, 5).forEach(result => {
                html += `
                    <a href="${result.url}" class="search-result-item" style="
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 12px 24px;
                        color: #fff;
                        text-decoration: none;
                        border-bottom: 1px solid rgba(255,255,255,0.05);
                        transition: background 0.2s;
                        cursor: pointer;
                    " onmouseover="this.style.background='rgba(176, 251, 165, 0.1)'" onmouseout="this.style.background='transparent'" onclick="event.preventDefault(); window.location.href='${result.url}'; document.getElementById('global-search-overlay').style.display='none';">
                        <span style="font-size: 20px;">${result.icon}</span>
                        <div style="flex: 1;">
                            <div style="font-weight: 600; margin-bottom: 2px;">${escapeHtml(result.title)}</div>
                            <div style="font-size: 12px; color: rgba(255,255,255,0.6);">${escapeHtml(result.subtitle)}</div>
                        </div>
                    </a>
                `;
            });
        });

        resultsContainer.innerHTML = html;
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Keyboard shortcut: Cmd/Ctrl+K
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            openSearch();
        }
    });

    // Add CSS animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from {
                transform: translateY(-20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

    // Export for manual opening
    window.openGlobalSearch = openSearch;
})();




