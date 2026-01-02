// ============================================
// JOBS LIST VIEW MODULE
// ============================================

/**
 * Render List view
 */
function renderList() {
    const tbody = document.getElementById('list-tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    
    const filteredJobs = window.filteredJobs || [];
    
    if (filteredJobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:40px;color:var(--text-secondary);">Žádné zakázky</td></tr>';
        return;
    }
    
    filteredJobs.forEach(job => {
        const tr = document.createElement('tr');
        const daysUntil = window.JobsUtils ? window.JobsUtils.getDaysUntilDeadline(job.deadline) : null;
        const deadlineClass = window.JobsUtils ? window.JobsUtils.getDeadlineBadgeClass(daysUntil) : '';
        const progress = job.progress || 0;
        
        const statusLabels = {
            new: 'Nové',
            active: 'Aktivní',
            paused: 'Pozastavené',
            completed: 'Dokončené'
        };
        
        const priorityLabels = {
            high: 'Vysoká',
            medium: 'Střední',
            low: 'Nízká'
        };
        
        const escapeHtml = window.JobsUtils ? window.JobsUtils.escapeHtml : (text) => text;
        const formatDate = window.JobsUtils ? window.JobsUtils.formatDate : (date) => date;
        
        tr.innerHTML = `
            <td>${job.id}</td>
            <td>${escapeHtml(job.title || 'Bez názvu')}</td>
            <td>${escapeHtml(job.client || '—')}</td>
            <td><span class="priority-badge ${job.status}">${statusLabels[job.status] || job.status}</span></td>
            <td><span class="priority-badge ${job.priority || 'medium'}">${priorityLabels[job.priority || 'medium']}</span></td>
            <td><span class="deadline-badge ${deadlineClass}">${formatDate(job.deadline)}</span></td>
            <td>
                <div class="progress-container" style="width:100px;margin:0;">
                    <div class="progress-bar" style="width: ${progress}%"></div>
                    <span class="progress-text">${progress}%</span>
                </div>
            </td>
            <td>
                <button class="btn-secondary" onclick="showJobDetail(${job.id})">Detail</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Export
window.JobsList = {
    renderList
};
