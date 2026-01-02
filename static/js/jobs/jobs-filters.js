// ============================================
// JOBS FILTERS MODULE
// ============================================

/**
 * Apply filters
 */
function applyFilters() {
    const jobs = window.jobs || [];
    const filters = window.filters || {};
    window.filteredJobs = jobs.filter(job => {
        // Vylepšené fulltextové vyhledávání s fuzzy matching
        if (filters.search) {
            const searchLower = filters.search.toLowerCase().trim();
            const searchTerms = searchLower.split(/\s+/).filter(t => t.length > 0);
            
            if (searchTerms.length === 0) {
                return true; // Prázdný dotaz = zobraz vše
            }
            
            // Vytvoř searchable text z všech polí (včetně code, note, city)
            const searchableText = [
                job.title || '',
                job.name || '', // fallback pro staré zakázky
                job.client || '',
                job.address || '',
                job.city || '',
                job.code || '',
                job.notes || '',
                job.note || '', // fallback
                job.type || '',
                job.manager || '',
                (job.team || []).join(' '),
                job.id?.toString() || '',
                (job.description || '').substring(0, 200) // první 200 znaků popisu
            ].join(' ').toLowerCase();
            
            // Vylepšené vyhledávání:
            // 1. Přesná shoda má vyšší prioritu
            // 2. Částečná shoda (fuzzy) pro delší termy
            const allTermsFound = searchTerms.every(term => {
                if (term.length < 2) return true; // Ignoruj velmi krátké termy
                
                // Přesná shoda
                if (searchableText.includes(term)) {
                    return true;
                }
                
                // Fuzzy matching pro termy delší než 3 znaky
                if (term.length >= 3) {
                    // Hledej částečné shody (např. "pra" najde "praha")
                    const regex = new RegExp(term.split('').join('.*'), 'i');
                    if (regex.test(searchableText)) {
                        return true;
                    }
                }
                
                return false;
            });
            
            if (!allTermsFound) {
                return false;
            }
        }
        
        // Status
        if (filters.status.length > 0 && !filters.status.includes(job.status)) {
            return false;
        }
        
        // Client
        if (filters.client && job.client !== filters.client) {
            return false;
        }
        
        // Manager
        if (filters.manager && job.manager !== filters.manager) {
            return false;
        }
        
        // Location
        if (filters.location && !job.address.toLowerCase().includes(filters.location.toLowerCase())) {
            return false;
        }
        
        // Priority
        if (filters.priority && job.priority !== filters.priority) {
            return false;
        }
        
        // Date range
        const jobDate = job.deadline || job.start_date || job.created_date;
        if (filters.dateFrom && jobDate && new Date(jobDate) < new Date(filters.dateFrom)) {
            return false;
        }
        if (filters.dateTo && jobDate && new Date(jobDate) > new Date(filters.dateTo)) {
            return false;
        }
        
        // Quick date filters
        if (filters.quickDateFilter) {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const jobDateObj = jobDate ? new Date(jobDate) : null;
            
            if (filters.quickDateFilter === 'today') {
                if (!jobDateObj || jobDateObj.toDateString() !== today.toDateString()) {
                    return false;
                }
            } else if (filters.quickDateFilter === 'week') {
                const weekStart = new Date(today);
                weekStart.setDate(today.getDate() - today.getDay());
                if (!jobDateObj || jobDateObj < weekStart) {
                    return false;
                }
            } else if (filters.quickDateFilter === 'month') {
                const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
                if (!jobDateObj || jobDateObj < monthStart) {
                    return false;
                }
            } else if (filters.quickDateFilter === 'overdue') {
                if (!jobDateObj || jobDateObj >= today || !job.deadline) {
                    return false;
                }
            }
        }
        
        // My active filter
        if (filters.myActive) {
            const currentUser = localStorage.getItem('currentUser') || '';
            const isMyJob = job.manager === currentUser || 
                           (job.team && job.team.includes(currentUser)) ||
                           job.status === 'active';
            if (!isMyJob) {
                return false;
            }
        }
        
        return true;
    });
}

/**
 * Populate filter dropdowns
 */
function populateFilters() {
    const jobs = window.jobs || [];
    // Clients
    const clients = [...new Set(jobs.map(j => j.client).filter(c => c && c !== '—'))];
    const clientSelect = document.getElementById('filter-client');
    if (clientSelect) {
        clientSelect.innerHTML = '<option value="">Všichni</option>';
        clients.forEach(client => {
            const option = document.createElement('option');
            option.value = client;
            option.textContent = client;
            clientSelect.appendChild(option);
        });
    }
    
    // Managers
    const managers = [...new Set(jobs.map(j => j.manager).filter(m => m && m !== '—'))];
    const managerSelect = document.getElementById('filter-manager');
    if (managerSelect) {
        managerSelect.innerHTML = '<option value="">Všichni</option>';
        managers.forEach(manager => {
            const option = document.createElement('option');
            option.value = manager;
            option.textContent = manager;
            managerSelect.appendChild(option);
        });
    }
}

// Export
window.JobsFilters = {
    applyFilters,
    populateFilters
};
