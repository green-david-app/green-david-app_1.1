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

// Export
window.JobsTimeline = {
    timelineZoom,
    getZoomLevel: () => timelineZoomLevel
};
