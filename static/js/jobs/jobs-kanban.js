// ============================================
// JOBS KANBAN VIEW MODULE
// ============================================

/**
 * Render Kanban board
 */
function renderKanban() {
    document.querySelectorAll('.cards-container').forEach(c => c.innerHTML = '');
    
    if (filteredJobs.length === 0 && jobs.length === 0) {
        ['new', 'active', 'paused', 'completed'].forEach(statusKey => {
            const container = document.getElementById(`cards-${statusKey}`);
            if (container) {
                for (let i = 0; i < 3; i++) {
                    container.appendChild(createSkeletonCard());
                }
            }
        });
        return;
    }
    
    filteredJobs.forEach(job => {
        const card = createJobCard(job);
        let statusKey = 'new';
        const statusLower = (job.status || '').toLowerCase();
        if (statusLower === 'aktivní' || statusLower === 'active' || statusLower === 'probíhá') {
            statusKey = 'active';
        } else if (statusLower === 'pozastavené' || statusLower === 'paused') {
            statusKey = 'paused';
        } else if (statusLower === 'dokončeno' || statusLower === 'completed' || statusLower === 'dokončené') {
            statusKey = 'completed';
        } else {
            statusKey = 'new';
        }
        const container = document.getElementById(`cards-${statusKey}`);
        if (container) {
            container.appendChild(card);
        }
    });
    
    requestAnimationFrame(() => {
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
            setTimeout(() => {
                lucide.createIcons();
            }, 50);
        }
    });
    
    updateColumnCounts();
}

/**
 * Update column counts
 */
function updateColumnCounts() {
    const counts = { new: 0, active: 0, paused: 0, completed: 0 };
    const values = { new: 0, active: 0, paused: 0, completed: 0 };
    
    filteredJobs.forEach(job => {
        if (counts.hasOwnProperty(job.status)) {
            counts[job.status]++;
            values[job.status] += job.budget || 0;
        }
    });
    
    Object.keys(counts).forEach(status => {
        const column = document.querySelector(`.kanban-column[data-status="${status}"]`);
        if (column) {
            const countEl = column.querySelector('.count');
            const valueEl = document.getElementById(`value-${status}`);
            if (countEl) countEl.textContent = counts[status];
            if (valueEl && window.JobsUtils) {
                valueEl.textContent = window.JobsUtils.formatCurrency(values[status]);
            }
        }
    });
}

// Export
window.JobsKanban = {
    renderKanban,
    updateColumnCounts
};
