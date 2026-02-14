/**
 * GPS Check-in/out System
 * Automatické zaznamenávání příchodu/odchodu na základě lokace
 */

class GPSTracker {
    constructor() {
        this.currentPosition = null;
        this.watchId = null;
        this.isTracking = false;
        this.checkInData = this.loadCheckInData();
        this.jobLocations = [];
        this.PROXIMITY_METERS = 100; // Vzdálenost pro auto check-in
    }
    
    loadCheckInData() {
        try {
            return JSON.parse(localStorage.getItem('gps-checkin-data')) || {};
        } catch(e) {
            return {};
        }
    }
    
    saveCheckInData() {
        localStorage.setItem('gps-checkin-data', JSON.stringify(this.checkInData));
    }
    
    async init() {
        debugLog('🛰️ GPS Tracker initializing...');
        
        if (!navigator.geolocation) {
            console.warn('Geolocation not supported');
            return;
        }
        
        // Load job locations
        await this.loadJobLocations();
        
        // Check current status
        this.updateUI();
        
        debugLog('✅ GPS Tracker ready');
    }
    
    async loadJobLocations() {
        try {
            const res = await fetch('/api/jobs');
            const data = await res.json();
            const jobs = Array.isArray(data) ? data : (data.jobs || []);
            
            // Filter jobs with addresses and geocode them
            this.jobLocations = jobs
                .filter(j => j.address && j.status !== 'completed')
                .map(j => ({
                    id: j.id,
                    name: j.client || j.name || `Zakázka #${j.id}`,
                    address: j.address,
                    lat: j.lat || null,
                    lng: j.lng || null
                }));
                
            debugLog(`Loaded ${this.jobLocations.length} job locations`);
        } catch(e) {
            console.error('Error loading jobs:', e);
        }
    }
    
    async getCurrentPosition() {
        return new Promise((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(
                pos => {
                    this.currentPosition = {
                        lat: pos.coords.latitude,
                        lng: pos.coords.longitude,
                        accuracy: pos.coords.accuracy,
                        timestamp: new Date().toISOString()
                    };
                    resolve(this.currentPosition);
                },
                err => reject(err),
                { enableHighAccuracy: true, timeout: 10000 }
            );
        });
    }
    
    // Calculate distance between two points (Haversine formula)
    calculateDistance(lat1, lng1, lat2, lng2) {
        const R = 6371e3; // Earth radius in meters
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lng2 - lng1) * Math.PI / 180;
        
        const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ/2) * Math.sin(Δλ/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        
        return R * c; // Distance in meters
    }
    
    // Find nearest job to current position
    findNearestJob(position) {
        if (!position || this.jobLocations.length === 0) return null;
        
        let nearest = null;
        let minDistance = Infinity;
        
        for (const job of this.jobLocations) {
            if (!job.lat || !job.lng) continue;
            
            const distance = this.calculateDistance(
                position.lat, position.lng,
                job.lat, job.lng
            );
            
            if (distance < minDistance) {
                minDistance = distance;
                nearest = { ...job, distance };
            }
        }
        
        return nearest;
    }
    
    // Check-in to a job
    async checkIn(jobId, position = null) {
        if (!position) {
            try {
                position = await this.getCurrentPosition();
            } catch(e) {
                console.error('Could not get position:', e);
            }
        }
        
        const now = new Date();
        const today = now.toISOString().split('T')[0];
        
        this.checkInData = {
            jobId: jobId,
            checkInTime: now.toISOString(),
            checkInPosition: position,
            date: today
        };
        
        this.saveCheckInData();
        
        // Log to server
        try {
            await fetch('/api/gps/checkin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: jobId,
                    check_in_time: now.toISOString(),
                    lat: position?.lat,
                    lng: position?.lng
                })
            });
        } catch(e) {
            console.error('Error logging check-in:', e);
        }
        
        this.updateUI();
        
        const job = this.jobLocations.find(j => j.id === jobId);
        if (typeof showNotification === 'function') {
            showNotification(`✅ Check-in: ${job?.name || 'Zakázka #' + jobId}`, 'success');
        }
        
        return this.checkInData;
    }
    
    // Check-out from current job
    async checkOut() {
        if (!this.checkInData.jobId) {
            console.warn('No active check-in');
            return null;
        }
        
        let position = null;
        try {
            position = await this.getCurrentPosition();
        } catch(e) {
            console.error('Could not get position:', e);
        }
        
        const now = new Date();
        const checkInTime = new Date(this.checkInData.checkInTime);
        const hoursWorked = (now - checkInTime) / (1000 * 60 * 60);
        
        const checkOutData = {
            ...this.checkInData,
            checkOutTime: now.toISOString(),
            checkOutPosition: position,
            hoursWorked: Math.round(hoursWorked * 100) / 100
        };
        
        // Log to server and create timesheet
        try {
            await fetch('/api/gps/checkout', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_id: checkOutData.jobId,
                    check_in_time: checkOutData.checkInTime,
                    check_out_time: checkOutData.checkOutTime,
                    hours_worked: checkOutData.hoursWorked,
                    lat: position?.lat,
                    lng: position?.lng
                })
            });
        } catch(e) {
            console.error('Error logging check-out:', e);
        }
        
        // Clear check-in data
        this.checkInData = {};
        this.saveCheckInData();
        
        this.updateUI();
        
        if (typeof showNotification === 'function') {
            showNotification(`🏁 Check-out: ${checkOutData.hoursWorked.toFixed(1)} hodin zaznamenáno`, 'success');
        }
        
        return checkOutData;
    }
    
    // Start background tracking
    startTracking() {
        if (this.watchId) return;
        
        this.isTracking = true;
        this.watchId = navigator.geolocation.watchPosition(
            pos => this.onPositionUpdate(pos),
            err => console.error('GPS error:', err),
            { enableHighAccuracy: true, maximumAge: 30000 }
        );
        
        debugLog('GPS tracking started');
    }
    
    stopTracking() {
        if (this.watchId) {
            navigator.geolocation.clearWatch(this.watchId);
            this.watchId = null;
        }
        this.isTracking = false;
        debugLog('GPS tracking stopped');
    }
    
    onPositionUpdate(pos) {
        this.currentPosition = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
            accuracy: pos.coords.accuracy,
            timestamp: new Date().toISOString()
        };
        
        // Check for auto check-in/out
        const nearest = this.findNearestJob(this.currentPosition);
        
        if (nearest && nearest.distance < this.PROXIMITY_METERS) {
            // Near a job site
            if (!this.checkInData.jobId) {
                // Auto check-in prompt
                this.showAutoCheckInPrompt(nearest);
            }
        } else if (this.checkInData.jobId && nearest && nearest.distance > this.PROXIMITY_METERS * 2) {
            // Left job site
            this.showAutoCheckOutPrompt();
        }
    }
    
    showAutoCheckInPrompt(job) {
        if (document.getElementById('gps-auto-prompt')) return;
        
        const prompt = document.createElement('div');
        prompt.id = 'gps-auto-prompt';
        prompt.className = 'gps-prompt';
        prompt.innerHTML = `
            <div class="gps-prompt-content">
                <div class="gps-prompt-icon">📍</div>
                <div class="gps-prompt-text">
                    <strong>Jsi u zakázky "${job.name}"</strong>
                    <span>Chceš se přihlásit?</span>
                </div>
                <div class="gps-prompt-actions">
                    <button class="gps-btn-yes" onclick="gpsTracker.checkIn(${job.id}); this.closest('.gps-prompt').remove();">
                        ✓ Check-in
                    </button>
                    <button class="gps-btn-no" onclick="this.closest('.gps-prompt').remove();">
                        ✕
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(prompt);
        
        // Auto-hide after 30s
        setTimeout(() => prompt.remove(), 30000);
    }
    
    showAutoCheckOutPrompt() {
        if (document.getElementById('gps-auto-prompt')) return;
        
        const prompt = document.createElement('div');
        prompt.id = 'gps-auto-prompt';
        prompt.className = 'gps-prompt';
        prompt.innerHTML = `
            <div class="gps-prompt-content">
                <div class="gps-prompt-icon">🚗</div>
                <div class="gps-prompt-text">
                    <strong>Opustil jsi místo zakázky</strong>
                    <span>Chceš se odhlásit?</span>
                </div>
                <div class="gps-prompt-actions">
                    <button class="gps-btn-yes" onclick="gpsTracker.checkOut(); this.closest('.gps-prompt').remove();">
                        ✓ Check-out
                    </button>
                    <button class="gps-btn-no" onclick="this.closest('.gps-prompt').remove();">
                        ✕
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(prompt);
        
        setTimeout(() => prompt.remove(), 30000);
    }
    
    // Get current status
    getStatus() {
        if (this.checkInData.jobId) {
            const job = this.jobLocations.find(j => j.id === this.checkInData.jobId);
            const checkInTime = new Date(this.checkInData.checkInTime);
            const elapsed = (new Date() - checkInTime) / (1000 * 60 * 60);
            
            return {
                status: 'checked-in',
                jobId: this.checkInData.jobId,
                jobName: job?.name || `Zakázka #${this.checkInData.jobId}`,
                checkInTime: checkInTime,
                elapsedHours: Math.round(elapsed * 100) / 100
            };
        }
        return { status: 'available' };
    }
    
    updateUI() {
        const container = document.getElementById('gps-status-widget');
        if (!container) return;
        
        const status = this.getStatus();
        
        if (status.status === 'checked-in') {
            container.innerHTML = `
                <div class="gps-widget checked-in">
                    <div class="gps-widget-header">
                        <span class="gps-status-dot active"></span>
                        <span>Na zakázce</span>
                    </div>
                    <div class="gps-widget-job">${status.jobName}</div>
                    <div class="gps-widget-time">
                        <span class="gps-elapsed" data-start="${status.checkInTime.toISOString()}">
                            ${status.elapsedHours.toFixed(1)}h
                        </span>
                        od ${status.checkInTime.toLocaleTimeString('cs-CZ', {hour: '2-digit', minute: '2-digit'})}
                    </div>
                    <button class="gps-checkout-btn" onclick="gpsTracker.checkOut()">
                        🏁 Check-out
                    </button>
                </div>
            `;
            
            // Update elapsed time every minute
            this.startElapsedTimer();
        } else {
            container.innerHTML = `
                <div class="gps-widget available">
                    <div class="gps-widget-header">
                        <span class="gps-status-dot"></span>
                        <span>Volný</span>
                    </div>
                    <button class="gps-checkin-btn" onclick="gpsTracker.showCheckInModal()">
                        📍 Check-in na zakázku
                    </button>
                </div>
            `;
        }
    }
    
    startElapsedTimer() {
        setInterval(() => {
            const el = document.querySelector('.gps-elapsed');
            if (!el) return;
            
            const start = new Date(el.dataset.start);
            const elapsed = (new Date() - start) / (1000 * 60 * 60);
            el.textContent = `${elapsed.toFixed(1)}h`;
        }, 60000);
    }
    
    showCheckInModal() {
        const modal = document.createElement('div');
        modal.className = 'gps-modal-overlay';
        modal.innerHTML = `
            <div class="gps-modal">
                <div class="gps-modal-header">
                    <h3>📍 Check-in na zakázku</h3>
                    <button class="gps-modal-close" onclick="this.closest('.gps-modal-overlay').remove()">×</button>
                </div>
                <div class="gps-modal-body">
                    <div class="gps-job-list">
                        ${this.jobLocations.length === 0 ? '<p>Žádné aktivní zakázky</p>' : ''}
                        ${this.jobLocations.map(job => `
                            <div class="gps-job-item" onclick="gpsTracker.checkIn(${job.id}); this.closest('.gps-modal-overlay').remove();">
                                <div class="gps-job-icon">📋</div>
                                <div class="gps-job-info">
                                    <div class="gps-job-name">${job.name}</div>
                                    <div class="gps-job-address">${job.address || 'Bez adresy'}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
}

// Inject styles
const gpsStyles = document.createElement('style');
gpsStyles.textContent = `
    .gps-widget {
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 12px;
        padding: 16px;
    }
    
    .gps-widget.checked-in {
        border-color: var(--mint, #4ade80);
        background: rgba(74, 222, 128, 0.05);
    }
    
    .gps-widget-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        color: var(--text-secondary, #9ca8b3);
        margin-bottom: 8px;
    }
    
    .gps-status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #6b7280;
    }
    
    .gps-status-dot.active {
        background: var(--mint, #4ade80);
        animation: gps-pulse 2s infinite;
    }
    
    @keyframes gps-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .gps-widget-job {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary, #e8eef2);
        margin-bottom: 4px;
    }
    
    .gps-widget-time {
        font-size: 14px;
        color: var(--text-secondary, #9ca8b3);
        margin-bottom: 12px;
    }
    
    .gps-elapsed {
        font-weight: 600;
        color: var(--mint, #4ade80);
        font-size: 18px;
    }
    
    .gps-checkin-btn, .gps-checkout-btn {
        width: 100%;
        padding: 12px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .gps-checkin-btn {
        background: var(--bg-elevated, #242a33);
        color: var(--text-primary, #e8eef2);
        border: 1px solid var(--border-primary, #2d3748);
    }
    
    .gps-checkin-btn:hover {
        border-color: var(--mint, #4ade80);
    }
    
    .gps-checkout-btn {
        background: var(--mint, #4ade80);
        color: #0a0e11;
    }
    
    .gps-checkout-btn:hover {
        background: #7bc47e;
    }
    
    /* Prompt */
    .gps-prompt {
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 10000;
        animation: gps-slide-up 0.3s ease;
    }
    
    @keyframes gps-slide-up {
        from { transform: translateX(-50%) translateY(20px); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
    }
    
    .gps-prompt-content {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px 20px;
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--mint, #4ade80);
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    
    .gps-prompt-icon {
        font-size: 28px;
    }
    
    .gps-prompt-text {
        display: flex;
        flex-direction: column;
    }
    
    .gps-prompt-text strong {
        color: var(--text-primary, #e8eef2);
        font-size: 14px;
    }
    
    .gps-prompt-text span {
        color: var(--text-secondary, #9ca8b3);
        font-size: 12px;
    }
    
    .gps-prompt-actions {
        display: flex;
        gap: 8px;
    }
    
    .gps-btn-yes {
        padding: 8px 16px;
        background: var(--mint, #4ade80);
        border: none;
        border-radius: 8px;
        color: #0a0e11;
        font-weight: 600;
        cursor: pointer;
    }
    
    .gps-btn-no {
        padding: 8px 12px;
        background: transparent;
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 8px;
        color: var(--text-secondary, #9ca8b3);
        cursor: pointer;
    }
    
    /* Modal */
    .gps-modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10000;
    }
    
    .gps-modal {
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 16px;
        width: 90%;
        max-width: 400px;
        max-height: 80vh;
        overflow: hidden;
    }
    
    .gps-modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid var(--border-primary, #2d3748);
    }
    
    .gps-modal-header h3 {
        margin: 0;
        font-size: 18px;
    }
    
    .gps-modal-close {
        background: none;
        border: none;
        color: var(--text-secondary, #9ca8b3);
        font-size: 24px;
        cursor: pointer;
    }
    
    .gps-modal-body {
        padding: 16px;
        max-height: 60vh;
        overflow-y: auto;
    }
    
    .gps-job-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .gps-job-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: var(--bg-elevated, #242a33);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .gps-job-item:hover {
        border-color: var(--mint, #4ade80);
    }
    
    .gps-job-icon {
        font-size: 24px;
    }
    
    .gps-job-name {
        font-weight: 600;
        color: var(--text-primary, #e8eef2);
    }
    
    .gps-job-address {
        font-size: 12px;
        color: var(--text-secondary, #9ca8b3);
    }
`;
document.head.appendChild(gpsStyles);

// Global instance
window.gpsTracker = new GPSTracker();
