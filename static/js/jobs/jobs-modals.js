// ============================================
// JOBS MODALS MODULE
// ============================================

/**
 * Show job detail modal
 */
function showJobDetail(jobId) {
    const jobs = window.jobs || [];
    const job = jobs.find(j => j.id === jobId);
    if (!job) return;
    
    window.currentJobId = jobId;
    document.getElementById('detail-title').textContent = job.title;
    const body = document.getElementById('detail-body');
    
    const escapeHtml = window.JobsUtils ? window.JobsUtils.escapeHtml : (text) => text || '';
    const formatDate = window.JobsUtils ? window.JobsUtils.formatDate : (date) => date || '—';
    
    body.innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-bottom:24px;">
            <div>
                <h4 style="color:var(--text-secondary);margin-bottom:8px;">Klient</h4>
                <p style="margin:0;">${escapeHtml(job.client)}</p>
            </div>
            <div>
                <h4 style="color:var(--text-secondary);margin-bottom:8px;">Lokace</h4>
                <p style="margin:0;">${escapeHtml(job.address)}</p>
            </div>
            <div>
                <h4 style="color:var(--text-secondary);margin-bottom:8px;">Deadline</h4>
                <p style="margin:0;">${formatDate(job.deadline)}</p>
            </div>
            <div>
                <h4 style="color:var(--text-secondary);margin-bottom:8px;">Status</h4>
                <p style="margin:0;"><span class="priority-badge ${job.status}">${job.status}</span></p>
            </div>
        </div>
        <div style="margin-bottom:24px;">
            <h4 style="color:var(--text-secondary);margin-bottom:8px;">Popis</h4>
            <p>${escapeHtml(job.notes || '—')}</p>
        </div>
        <div style="margin-bottom:24px;">
            <h4 style="color:var(--text-secondary);margin-bottom:8px;">Progress</h4>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${job.progress || 0}%"></div>
            </div>
            <p style="margin-top:8px;color:var(--text-secondary);">${job.progress || 0}% dokončeno</p>
        </div>
    `;
    const modal = document.getElementById('job-detail-modal');
    if (modal) modal.classList.add('active');
}

/**
 * Open edit job modal
 */
function openEditJobModal(jobId) {
    const jobs = window.jobs || [];
    const job = jobs.find(j => j.id === jobId);
    if (!job) return;
    
    window.currentJobId = jobId;
    const escapeHtml = window.JobsUtils ? window.JobsUtils.escapeHtml : (text) => text || '';
    document.getElementById('edit-job-title').textContent = `Upravit zakázku: ${escapeHtml(job.title)}`;
    
    const statusMap = {
        'new': 'Plán',
        'active': 'Aktivní',
        'paused': 'Pozastavené',
        'completed': 'Dokončeno'
    };
    
    document.getElementById('edit-title').value = job.title || '';
    document.getElementById('edit-client').value = job.client || '';
    document.getElementById('edit-address').value = job.address || '';
    document.getElementById('edit-deadline').value = job.deadline ? job.deadline.split('T')[0] : '';
    document.getElementById('edit-created-date').value = job.created_date ? job.created_date.split('T')[0] : '';
    document.getElementById('edit-start-date').value = job.start_date ? job.start_date.split('T')[0] : '';
    document.getElementById('edit-status').value = statusMap[job.status] || 'Plán';
    document.getElementById('edit-progress').value = job.progress || 0;
    document.getElementById('edit-notes').value = job.notes || '';
    
    const modal = document.getElementById('edit-job-modal');
    if (modal) modal.classList.add('active');
}

// Export
window.JobsModals = {
    showJobDetail,
    openEditJobModal
};
