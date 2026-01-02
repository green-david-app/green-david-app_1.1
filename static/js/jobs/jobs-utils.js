// ============================================
// JOBS UTILS MODULE
// ============================================

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('cs-CZ', { style: 'currency', currency: 'CZK' }).format(amount);
}

/**
 * Format date
 */
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleDateString('cs-CZ');
}

/**
 * Get days until deadline
 */
function getDaysUntilDeadline(deadline) {
    if (!deadline) return null;
    const days = Math.ceil((new Date(deadline) - new Date()) / (1000 * 60 * 60 * 24));
    return days;
}

/**
 * Get deadline badge class
 */
function getDeadlineBadgeClass(days) {
    if (days === null) return 'muted';
    if (days < 0) return 'danger';
    if (days <= 7) return 'danger';
    if (days <= 14) return 'warning';
    if (days <= 30) return 'ok';
    return 'muted';
}

/**
 * Get job type icon
 */
function getJobTypeIcon(type) {
    const icons = {
        reconstruction: '<svg class="job-type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        'new-build': '<svg class="job-type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>',
        repair: '<svg class="job-type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>',
        renovation: '<svg class="job-type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
        maintenance: '<svg class="job-type-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'
    };
    return icons[type] || '';
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
 * Map status to Kanban
 */
function mapStatusToKanban(status) {
    if (!status) return 'new';
    const statusLower = status.toLowerCase();
    if (statusLower.includes('nov') || statusLower.includes('plán')) return 'new';
    if (statusLower.includes('aktiv') || statusLower.includes('probíhá')) return 'active';
    if (statusLower.includes('pozastav') || statusLower.includes('pause')) return 'paused';
    if (statusLower.includes('dokon') || statusLower.includes('completed')) return 'completed';
    return 'new';
}

/**
 * Calculate progress
 */
function calculateProgress(job) {
    return job.progress || 0;
}

// Export
window.JobsUtils = {
    formatCurrency,
    formatDate,
    getDaysUntilDeadline,
    getDeadlineBadgeClass,
    getJobTypeIcon,
    escapeHtml,
    mapStatusToKanban,
    calculateProgress
};

