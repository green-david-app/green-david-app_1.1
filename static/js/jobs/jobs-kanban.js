// ============================================
// JOBS KANBAN VIEW MODULE
// ============================================

/**
 * Render Kanban board
 */
function renderKanban() {
    document.querySelectorAll('.cards-container').forEach(c => c.innerHTML = '');
    
    const jobs = window.jobs || [];
    const filteredJobs = window.filteredJobs || [];
    
    // DEBUG
    console.log('=== renderKanban DEBUG ===');
    console.log('jobs.length:', jobs.length);
    console.log('filteredJobs.length:', filteredJobs.length);
    
    // Skeleton loading - jen když nemáme žádná data (initial load)
    if (jobs.length === 0) {
        ['new', 'active', 'paused', 'completed'].forEach(statusKey => {
            const container = document.getElementById(`cards-${statusKey}`);
            if (container) {
                for (let i = 0; i < 2; i++) {
                    const skeleton = typeof createSkeletonCard === 'function' ? createSkeletonCard() : null;
                    if (skeleton) container.appendChild(skeleton);
                }
            }
        });
        return;
    }
    
    // Žádné výsledky po filtrování - zobraz empty state
    if (filteredJobs.length === 0) {
        const kanbanBoard = document.querySelector('.kanban-board') || document.getElementById('kanban-view');
        if (kanbanBoard) {
            const emptyState = document.createElement('div');
            emptyState.style.cssText = 'grid-column: 1/-1; padding: 60px 20px; text-align: center;';
            emptyState.innerHTML = `
                <svg style="width: 64px; height: 64px; color: var(--text-tertiary); margin: 0 auto 16px; display: block;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="m21 21-4.35-4.35"></path>
                </svg>
                <div style="font-size: 18px; color: var(--text-secondary); margin-bottom: 8px;">
                    Žádné zakázky odpovídající filtrům
                </div>
                <div style="font-size: 14px; color: var(--text-tertiary);">
                    Zkuste změnit filtry nebo vytvořit novou zakázku
                </div>
            `;
            kanbanBoard.insertBefore(emptyState, kanbanBoard.firstChild);
        }
        return;
    }
    
    // Normální rendering karet
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
    const filteredJobs = window.filteredJobs || [];
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
