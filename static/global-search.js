/* ============================================================================
 * GLOBAL SEARCH COMPONENT
 * ============================================================================
 * Moderní vyhledávací komponenta s real-time resultsem
 */

class GlobalSearch {
    constructor() {
        this.searchInput = null;
        this.resultsDropdown = null;
        this.debounceTimer = null;
        this.isOpen = false;
        
        this.init();
    }
    
    init() {
        // Vytvoř search bar v headeru
        this.createSearchBar();
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Cmd+K nebo Ctrl+K
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                this.focus();
            }
            
            // ESC zavře dropdown
            if (e.key === 'Escape' && this.isOpen) {
                this.closeResults();
            }
        });
        
        // Zavři dropdown při kliknutí mimo
        document.addEventListener('click', (e) => {
            if (this.searchInput && this.resultsDropdown && !this.searchInput.contains(e.target) && !this.resultsDropdown.contains(e.target)) {
                this.closeResults();
            }
        });
    }
    
    createSearchBar() {
        // Najdi header search container
        const container = document.querySelector('.global-search-container');
        if (!container) {
            console.error('Global search container not found');
            return;
        }
        
        // Input field
        this.searchInput = document.createElement('input');
        this.searchInput.type = 'text';
        this.searchInput.className = 'global-search-input';
        this.searchInput.placeholder = 'Vyhledat v aplikaci... (⌘K)';
        this.searchInput.addEventListener('input', (e) => this.handleInput(e));
        this.searchInput.addEventListener('focus', () => {
            if (this.searchInput.value.trim().length >= 2) {
                this.openResults();
            }
        });

        // Enter => full page results
        this.searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const q = this.searchInput.value.trim();
                if (q.length >= 2) {
                    window.location.href = `/search.html?q=${encodeURIComponent(q)}`;
                }
            }
        });
        
        // Results dropdown
        this.resultsDropdown = document.createElement('div');
        this.resultsDropdown.className = 'global-search-results';
        this.resultsDropdown.style.display = 'none';
        
        container.innerHTML = '';
        container.appendChild(this.searchInput);
        container.appendChild(this.resultsDropdown);
    }
    
    handleInput(e) {
        const query = e.target.value.trim();
        
        // Clear previous timer
        clearTimeout(this.debounceTimer);
        
        if (query.length < 2) {
            this.closeResults();
            return;
        }
        
        // Debounce search (300ms)
        this.debounceTimer = setTimeout(() => {
            this.performSearch(query);
        }, 300);
    }
    
    async performSearch(query) {
        try {
            const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            
            if (data.ok) {
                this.displayResults(data.results, data.total, query);
            }
        } catch (error) {
            console.error('Search error:', error);
        }
    }
    
    displayResults(results, total, query) {
        if (total === 0) {
            this.resultsDropdown.innerHTML = `
                <div class="search-no-results">
                    <i data-lucide="search-x"></i>
                    <p>Žádné výsledky pro "${query}"</p>
                </div>
            `;
            this.openResults();
            lucide.createIcons();
            return;
        }
        
        let html = '';
        
        // Zakázky
        if (results.jobs.length > 0) {
            html += '<div class="search-category">';
            html += '<h4><i data-lucide="briefcase"></i> Zakázky</h4>';
            results.jobs.forEach(job => {
                html += `
                    <a href="/jobs.html?id=${job.id}" class="search-result-item">
                        <div class="result-title">${this.highlight(job.name, query)}</div>
                        <div class="result-meta">${job.customer || ''} • ${job.status}</div>
                    </a>
                `;
            });
            html += '</div>';
        }
        
        // Úkoly
        if (results.tasks.length > 0) {
            html += '<div class="search-category">';
            html += '<h4><i data-lucide="check-square"></i> Úkoly</h4>';
            results.tasks.forEach(task => {
                html += `
                    <a href="/tasks.html?id=${task.id}" class="search-result-item">
                        <div class="result-title">${this.highlight(task.title, query)}</div>
                        <div class="result-meta">${task.job_name || ''} • ${this.translateStatus(task.status)}</div>
                    </a>
                `;
            });
            html += '</div>';
        }
        
        // Issues
        if (results.issues.length > 0) {
            html += '<div class="search-category">';
            html += '<h4><i data-lucide="alert-circle"></i> Issues</h4>';
            results.issues.forEach(issue => {
                html += `
                    <a href="/jobs.html?id=${issue.job_id}" class="search-result-item">
                        <div class="result-title">${this.highlight(issue.title, query)}</div>
                        <div class="result-meta">${issue.job_name || ''} • ${this.translateType(issue.type)}</div>
                    </a>
                `;
            });
            html += '</div>';
        }
        
        // Zaměstnanci
        if (results.employees.length > 0) {
            html += '<div class="search-category">';
            html += '<h4><i data-lucide="users"></i> Zaměstnanci</h4>';
            results.employees.forEach(emp => {
                html += `
                    <a href="/employees.html?id=${emp.id}" class="search-result-item">
                        <div class="result-title">${this.highlight(emp.name, query)}</div>
                        <div class="result-meta">${emp.email || ''} • ${emp.role}</div>
                    </a>
                `;
            });
            html += '</div>';
        }
        
        html += `<a class="search-footer" href="/search.html?q=${encodeURIComponent(query)}">${total} výsledků – zobrazit vše</a>`;
        
        this.resultsDropdown.innerHTML = html;
        this.openResults();
        lucide.createIcons();
    }
    
    highlight(text, query) {
        if (!text) return '';
        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark>$1</mark>');
    }
    
    translateStatus(status) {
        const map = {
            'pending': 'Čeká',
            'in_progress': 'Probíhá',
            'completed': 'Hotovo',
            'blocked': 'Blokováno'
        };
        return map[status] || status;
    }
    
    translateType(type) {
        const map = {
            'blocker': 'Blokující',
            'quality': 'Kvalita',
            'safety': 'Bezpečnost',
            'note': 'Poznámka'
        };
        return map[type] || type;
    }
    
    openResults() {
        this.resultsDropdown.style.display = 'block';
        this.isOpen = true;
    }
    
    closeResults() {
        this.resultsDropdown.style.display = 'none';
        this.isOpen = false;
    }
    
    focus() {
        this.searchInput.focus();
        this.searchInput.select();
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.globalSearch = new GlobalSearch();
    });
} else {
    window.globalSearch = new GlobalSearch();
}
