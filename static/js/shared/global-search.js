// ============================================
// GLOBAL SEARCH MODULE
// ============================================

let searchIndex = [];
let selectedIndex = -1;
let currentResults = [];

/**
 * Open global search overlay
 */
function openGlobalSearch() {
    const overlay = document.getElementById('global-search-overlay');
    const input = document.getElementById('global-search-input');
    
    if (overlay) {
        overlay.classList.add('active');
        if (input) {
            setTimeout(() => input.focus(), 100);
        }
    }
}

/**
 * Close global search overlay
 */
function closeGlobalSearch() {
    const overlay = document.getElementById('global-search-overlay');
    const input = document.getElementById('global-search-input');
    
    if (overlay) {
        overlay.classList.remove('active');
    }
    if (input) {
        input.value = '';
    }
    
    selectedIndex = -1;
    currentResults = [];
    renderResults([]);
}

/**
 * Build search index from API data
 */
async function buildSearchIndex() {
    try {
        searchIndex = [];
        
        // Load jobs
        try {
            const jobsRes = await fetch('/api/jobs');
            if (jobsRes.ok) {
                const jobsData = await jobsRes.json();
                const jobs = jobsData.jobs || [];
                
                jobs.forEach(job => {
                    searchIndex.push({
                        type: 'job',
                        id: job.id,
                        title: job.title || job.name || `Zakázka ${job.id}`,
                        subtitle: `${job.client || '—'} • ${job.city || job.address || '—'}`,
                        url: `/jobs.html#job-${job.id}`,
                        content: `${job.title || ''} ${job.client || ''} ${job.city || job.address || ''} ${job.note || ''}`.toLowerCase()
                    });
                });
            }
        } catch (error) {
            console.warn('Failed to load jobs for search:', error);
        }
        
        // Load employees
        try {
            const empRes = await fetch('/api/employees');
            if (empRes.ok) {
                const empData = await empRes.json();
                const employees = empData.employees || [];
                
                employees.forEach(emp => {
                    searchIndex.push({
                        type: 'employee',
                        id: emp.id,
                        title: emp.name || `Zaměstnanec ${emp.id}`,
                        subtitle: emp.role || '—',
                        url: `/employees.html#emp-${emp.id}`,
                        content: `${emp.name || ''} ${emp.role || ''} ${emp.email || ''}`.toLowerCase()
                    });
                });
            }
        } catch (error) {
            console.warn('Failed to load employees for search:', error);
        }
        
        // Load tasks (optional)
        try {
            const tasksRes = await fetch('/api/tasks');
            if (tasksRes.ok) {
                const tasksData = await tasksRes.json();
                const tasks = tasksData.tasks || [];
                
                tasks.forEach(task => {
                    searchIndex.push({
                        type: 'task',
                        id: task.id,
                        title: task.title || task.name || `Úkol ${task.id}`,
                        subtitle: task.status || '—',
                        url: `/tasks.html#task-${task.id}`,
                        content: `${task.title || ''} ${task.description || ''}`.toLowerCase()
                    });
                });
            }
        } catch (error) {
            console.warn('Failed to load tasks for search:', error);
        }
        
        console.log(`Search index built: ${searchIndex.length} items`);
    } catch (error) {
        console.error('Error building search index:', error);
    }
}

/**
 * Perform search query
 */
function performSearch(query) {
    if (!query || query.trim().length < 2) {
        renderResults([]);
        return;
    }
    
    const queryLower = query.toLowerCase().trim();
    const queryTerms = queryLower.split(/\s+/);
    
    // Filter results
    const results = searchIndex.filter(item => {
        // All terms must match
        return queryTerms.every(term => item.content.includes(term));
    });
    
    // Group by type
    const grouped = {};
    results.forEach(item => {
        if (!grouped[item.type]) {
            grouped[item.type] = [];
        }
        grouped[item.type].push(item);
    });
    
    currentResults = results;
    selectedIndex = -1;
    renderResults(grouped);
}

/**
 * Render search results
 */
function renderResults(grouped) {
    const container = document.getElementById('global-search-results');
    if (!container) return;
    
    if (!grouped || Object.keys(grouped).length === 0) {
        container.innerHTML = `
            <div class="search-empty">
                <p>Nic nenalezeno</p>
            </div>
        `;
        return;
    }
    
    const typeLabels = {
        job: 'ZAKÁZKY',
        employee: 'ZAMĚSTNANCI',
        task: 'ÚKOLY'
    };
    
    const typeIcons = {
        job: '📋',
        employee: '👤',
        task: '✅'
    };
    
    let html = '';
    
    // Render each group
    Object.keys(grouped).forEach(type => {
        const items = grouped[type];
        html += `
            <div class="search-result-group">
                <div class="search-result-group-title">${typeLabels[type] || type.toUpperCase()}</div>
        `;
        
        items.forEach((item, index) => {
            html += `
                <div class="search-result-item" 
                     data-index="${index}" 
                     onclick="selectSearchResult('${item.url}')"
                     onmouseenter="highlightSearchResult(${index})">
                    <div class="search-result-icon">${typeIcons[type] || '📄'}</div>
                    <div class="search-result-content">
                        <div class="search-result-title">${escapeHtml(item.title)}</div>
                        <div class="search-result-subtitle">${escapeHtml(item.subtitle)}</div>
                    </div>
                </div>
            `;
        });
        
        html += `</div>`;
    });
    
    container.innerHTML = html;
}

/**
 * Highlight search result
 */
function highlightSearchResult(index) {
    selectedIndex = index;
    document.querySelectorAll('.search-result-item').forEach((item, i) => {
        item.classList.toggle('selected', i === index);
    });
}

/**
 * Select search result and navigate
 */
function selectSearchResult(url) {
    closeGlobalSearch();
    window.location.href = url;
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Navigate results with keyboard
 */
function navigateResults(direction) {
    if (currentResults.length === 0) return;
    
    if (direction === 'up') {
        selectedIndex = selectedIndex > 0 ? selectedIndex - 1 : currentResults.length - 1;
    } else if (direction === 'down') {
        selectedIndex = selectedIndex < currentResults.length - 1 ? selectedIndex + 1 : 0;
    }
    
    highlightSearchResult(selectedIndex);
    
    // Scroll into view
    const selectedItem = document.querySelector(`.search-result-item[data-index="${selectedIndex}"]`);
    if (selectedItem) {
        selectedItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
}

/**
 * Initialize global search
 */
function initGlobalSearch() {
    // Build search index on load
    buildSearchIndex();
    
    // Input listener
    const input = document.getElementById('global-search-input');
    if (input) {
        input.addEventListener('input', (e) => {
            performSearch(e.target.value);
        });
        
        // Keyboard navigation
        input.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                navigateResults('down');
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                navigateResults('up');
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (selectedIndex >= 0 && currentResults[selectedIndex]) {
                    selectSearchResult(currentResults[selectedIndex].url);
                }
            } else if (e.key === 'Escape') {
                e.preventDefault();
                closeGlobalSearch();
            }
        });
    }
    
    // Global keyboard shortcut (⌘K / Ctrl+K)
    document.addEventListener('keydown', (e) => {
        // Don't trigger if typing in input/textarea
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            openGlobalSearch();
        }
    });
    
    // Close on backdrop click
    const backdrop = document.querySelector('.search-overlay-backdrop');
    if (backdrop) {
        backdrop.addEventListener('click', closeGlobalSearch);
    }
}

// Export functions globally
window.openGlobalSearch = openGlobalSearch;
window.closeGlobalSearch = closeGlobalSearch;
window.selectSearchResult = selectSearchResult;
window.highlightSearchResult = highlightSearchResult;

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGlobalSearch);
} else {
    initGlobalSearch();
}

