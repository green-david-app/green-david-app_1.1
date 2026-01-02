// ============================================
// JOBS TIMELINE VIEW MODULE
// ============================================

let timelineZoomLevel = 'month'; // 'month', 'quarter', 'year'

/**
 * Timeline zoom
 */
function timelineZoom(level) {
    timelineZoomLevel = level;
    document.querySelectorAll('.timeline-zoom-button').forEach(btn => {
        btn.classList.remove('active');
    });
    const activeBtn = document.getElementById(`zoom-${level}`);
    if (activeBtn) activeBtn.classList.add('active');
    renderTimeline();
}

/**
 * Render Timeline view
 */
function renderTimeline() {
    const container = document.getElementById('timeline-container');
    if (!container) {
        console.warn('Timeline container not found');
        return;
    }

    const filteredJobs = window.filteredJobs || [];
    if (filteredJobs.length === 0) {
        container.innerHTML = '<div style="padding:40px;text-align:center;color:var(--text-secondary);">Žádné zakázky k zobrazení</div>';
        return;
    }

    // Urči časový rozsah podle zoom levelu
    const today = new Date();
    let startDate, endDate;
    
    if (timelineZoomLevel === 'month') {
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);
    } else if (timelineZoomLevel === 'quarter') {
        const quarter = Math.floor(today.getMonth() / 3);
        startDate = new Date(today.getFullYear(), quarter * 3, 1);
        endDate = new Date(today.getFullYear(), (quarter + 1) * 3, 0);
    } else { // year
        startDate = new Date(today.getFullYear(), 0, 1);
        endDate = new Date(today.getFullYear(), 11, 31);
    }

    // Vytvoř pole všech dní v rozsahu
    const days = [];
    const currentDate = new Date(startDate);
    while (currentDate <= endDate) {
        days.push(new Date(currentDate));
        currentDate.setDate(currentDate.getDate() + 1);
    }

    // Vytvoř měsíce pro header
    const months = [];
    const monthSet = new Set();
    days.forEach(day => {
        const monthKey = `${day.getFullYear()}-${day.getMonth()}`;
        if (!monthSet.has(monthKey)) {
            monthSet.add(monthKey);
            months.push({
                date: new Date(day),
                days: days.filter(d => d.getFullYear() === day.getFullYear() && d.getMonth() === day.getMonth()).length
            });
        }
    });

    // Vypočítej šířku jednoho dne v pixelech
    const dayWidth = timelineZoomLevel === 'month' ? 30 : timelineZoomLevel === 'quarter' ? 10 : 3;
    const totalWidth = days.length * dayWidth;

    // Vytvoř HTML pro timeline
    let html = '<div class="timeline-scroll" style="overflow-x:auto;overflow-y:visible;">';
    html += '<div class="timeline-grid" style="position:relative;width:' + totalWidth + 'px;min-height:400px;">';
    
    // Header s měsíci
    html += '<div class="timeline-header-row" style="position:sticky;top:0;z-index:10;background:var(--bg-secondary);border-bottom:1px solid var(--border-primary);padding:8px 0;">';
    months.forEach(month => {
        const monthStart = new Date(month.date.getFullYear(), month.date.getMonth(), 1);
        const monthIndex = days.findIndex(d => d.getTime() === monthStart.getTime());
        const left = monthIndex * dayWidth;
        html += `<div style="position:absolute;left:${left}px;width:${month.days * dayWidth}px;text-align:center;font-weight:600;color:var(--text-primary);">${month.date.toLocaleDateString('cs-CZ', {month:'long', year:'numeric'})}</div>`;
    });
    html += '</div>';

    // Dny v headeru
    html += '<div class="timeline-days-row" style="position:sticky;top:40px;z-index:9;background:var(--bg-secondary);border-bottom:1px solid var(--border-primary);padding:4px 0;">';
    days.forEach((day, index) => {
        const isWeekend = day.getDay() === 0 || day.getDay() === 6;
        const isToday = day.toDateString() === today.toDateString();
        html += `<div style="position:absolute;left:${index * dayWidth}px;width:${dayWidth}px;text-align:center;font-size:11px;color:${isWeekend ? 'var(--text-tertiary)' : isToday ? 'var(--mint)' : 'var(--text-secondary)'};border-right:1px solid var(--border-primary);${isToday ? 'background:rgba(159,212,161,0.1);' : ''}">${day.getDate()}</div>`;
    });
    html += '</div>';

    // Zakázky jako časové pruhy
    filteredJobs.forEach((job, jobIndex) => {
        const jobStart = job.start_date ? new Date(job.start_date) : (job.created_date ? new Date(job.created_date) : new Date(job.deadline));
        const jobEnd = job.deadline ? new Date(job.deadline) : new Date(jobStart.getTime() + 7 * 24 * 60 * 60 * 1000); // default 7 dní
        
        if (!jobStart || isNaN(jobStart.getTime())) return;
        
        const startIndex = days.findIndex(d => d.toDateString() === jobStart.toDateString());
        const endIndex = days.findIndex(d => d.toDateString() === jobEnd.toDateString());
        
        if (startIndex === -1 && endIndex === -1) return;
        
        const left = startIndex >= 0 ? startIndex * dayWidth : 0;
        const width = (endIndex >= 0 ? endIndex : days.length - 1) * dayWidth - left + dayWidth;
        const top = 80 + jobIndex * 50;
        
        const statusColors = {
            new: '#3b82f6',
            active: '#9FD4A1',
            paused: '#f59e0b',
            completed: '#6b7280'
        };
        
        const color = statusColors[job.status] || '#3b82f6';
        const formatDate = window.JobsUtils ? window.JobsUtils.formatDate : (d) => d || '—';
        
        html += `<div class="timeline-job-bar" style="position:absolute;left:${left}px;top:${top}px;width:${Math.max(width, dayWidth)}px;height:40px;background:${color};border-radius:4px;padding:4px 8px;cursor:pointer;box-shadow:0 2px 4px rgba(0,0,0,0.2);" onclick="if(window.openJobDetail) window.openJobDetail(${job.id})" title="${job.title || 'Bez názvu'}">`;
        html += `<div style="font-weight:600;font-size:12px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${(job.title || 'Bez názvu').substring(0, 20)}</div>`;
        html += `<div style="font-size:10px;color:rgba(255,255,255,0.8);">${formatDate(job.deadline)}</div>`;
        html += '</div>';
    });

    html += '</div>'; // timeline-grid
    html += '</div>'; // timeline-scroll
    
    container.innerHTML = html;
}

// Export
window.JobsTimeline = {
    timelineZoom,
    renderTimeline,
    getZoomLevel: () => timelineZoomLevel
};
