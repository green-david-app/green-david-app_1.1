/**
 * Smart Notifications System
 * - Push notifications support
 * - Automatic deadline reminders
 * - Weather alerts for outdoor work
 * - Customizable notification preferences
 */

class SmartNotifications {
    constructor() {
        this.settings = this.loadSettings();
        this.checkInterval = null;
        this.lastCheck = {};
        
        // Default notification sounds (using Web Audio API)
        this.audioContext = null;
    }
    
    loadSettings() {
        try {
            const saved = localStorage.getItem('smart-notifications-settings');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {
            console.error('Error loading notification settings:', e);
        }
        
        return {
            enabled: true,
            pushEnabled: false,
            sound: true,
            // Reminder times (in hours before deadline)
            deadlineReminders: [24, 2],
            // Weather alerts
            weatherAlerts: {
                enabled: true,
                rainWarning: true,
                coldWarning: true, // Below 5°C
                heatWarning: true // Above 30°C
            },
            // Daily summary
            dailySummary: {
                enabled: true,
                time: '08:00'
            },
            // Low stock alerts
            lowStockAlerts: true,
            // Quiet hours
            quietHours: {
                enabled: false,
                start: '22:00',
                end: '07:00'
            }
        };
    }
    
    saveSettings() {
        try {
            localStorage.setItem('smart-notifications-settings', JSON.stringify(this.settings));
        } catch (e) {
            console.error('Error saving notification settings:', e);
        }
    }
    
    async init() {
        console.log('🔔 Smart Notifications initializing...');
        
        // Request push notification permission if enabled
        if (this.settings.pushEnabled) {
            await this.requestPushPermission();
        }
        
        // Start background checks
        this.startBackgroundChecks();
        
        // Register service worker for push notifications
        this.registerServiceWorker();
        
        console.log('✅ Smart Notifications ready');
    }
    
    async requestPushPermission() {
        if (!('Notification' in window)) {
            console.warn('Push notifications not supported');
            return false;
        }
        
        if (Notification.permission === 'granted') {
            return true;
        }
        
        if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            return permission === 'granted';
        }
        
        return false;
    }
    
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw-notifications.js');
                console.log('ServiceWorker registered:', registration.scope);
            } catch (e) {
                console.warn('ServiceWorker registration failed:', e);
            }
        }
    }
    
    startBackgroundChecks() {
        // Clear existing interval
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
        }
        
        // Check every 5 minutes
        this.checkInterval = setInterval(() => {
            this.runChecks();
        }, 5 * 60 * 1000);
        
        // Initial check
        setTimeout(() => this.runChecks(), 3000);
    }
    
    async runChecks() {
        if (!this.settings.enabled) return;
        if (this.isQuietHours()) return;
        
        console.log('🔍 Running notification checks...');
        
        try {
            // Check deadlines
            await this.checkDeadlines();
            
            // Check weather
            if (this.settings.weatherAlerts.enabled) {
                await this.checkWeather();
            }
            
            // Check low stock
            if (this.settings.lowStockAlerts) {
                await this.checkLowStock();
            }
            
            // Daily summary
            if (this.settings.dailySummary.enabled) {
                this.checkDailySummary();
            }
        } catch (e) {
            console.error('Error in notification checks:', e);
        }
    }
    
    isQuietHours() {
        if (!this.settings.quietHours.enabled) return false;
        
        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        
        const [startH, startM] = this.settings.quietHours.start.split(':').map(Number);
        const [endH, endM] = this.settings.quietHours.end.split(':').map(Number);
        
        const startTime = startH * 60 + startM;
        const endTime = endH * 60 + endM;
        
        if (startTime < endTime) {
            return currentTime >= startTime && currentTime < endTime;
        } else {
            // Overnight quiet hours (e.g., 22:00 - 07:00)
            return currentTime >= startTime || currentTime < endTime;
        }
    }
    
    async checkDeadlines() {
        try {
            const response = await fetch('/api/tasks');
            const data = await response.json();
            const tasks = Array.isArray(data) ? data : (data.tasks || []);
            
            const now = new Date();
            
            tasks.forEach(task => {
                if (!task.deadline || task.status === 'done') return;
                
                const deadline = new Date(task.deadline);
                const hoursUntil = (deadline - now) / (1000 * 60 * 60);
                
                this.settings.deadlineReminders.forEach(reminderHours => {
                    // Check if we should send this reminder
                    if (hoursUntil > 0 && hoursUntil <= reminderHours) {
                        const checkKey = `deadline-${task.id}-${reminderHours}h`;
                        
                        // Don't send duplicate reminders
                        if (!this.lastCheck[checkKey] || (now - this.lastCheck[checkKey]) > 12 * 60 * 60 * 1000) {
                            this.sendNotification({
                                title: '⏰ Blížící se termín',
                                body: `${task.title} - termín za ${Math.round(hoursUntil)} hodin`,
                                icon: '⏰',
                                tag: checkKey,
                                data: { url: '/tasks.html' }
                            });
                            this.lastCheck[checkKey] = now.getTime();
                        }
                    }
                });
                
                // Overdue tasks
                if (hoursUntil < 0 && hoursUntil > -24) {
                    const checkKey = `overdue-${task.id}`;
                    if (!this.lastCheck[checkKey]) {
                        this.sendNotification({
                            title: '🚨 Prošlý termín!',
                            body: `${task.title} měl být dokončen`,
                            icon: '🚨',
                            tag: checkKey,
                            urgent: true,
                            data: { url: '/tasks.html' }
                        });
                        this.lastCheck[checkKey] = now.getTime();
                    }
                }
            });
        } catch (e) {
            console.error('Error checking deadlines:', e);
        }
    }
    
    async checkWeather() {
        try {
            const response = await fetch('/api/weather');
            const weather = await response.json();
            
            if (!weather || !weather.current) return;
            
            const temp = weather.current.temperature;
            const condition = weather.current.condition?.toLowerCase() || '';
            const checkKey = `weather-${new Date().toDateString()}`;
            
            if (this.lastCheck[checkKey]) return;
            
            // Rain warning
            if (this.settings.weatherAlerts.rainWarning && 
                (condition.includes('rain') || condition.includes('déšť') || condition.includes('bouřka'))) {
                this.sendNotification({
                    title: '🌧️ Upozornění na počasí',
                    body: `Očekává se ${weather.current.description || 'déšť'} - zvažte plánování venkovních prací`,
                    icon: '🌧️',
                    tag: checkKey + '-rain'
                });
                this.lastCheck[checkKey] = Date.now();
            }
            
            // Cold warning
            if (this.settings.weatherAlerts.coldWarning && temp < 5) {
                this.sendNotification({
                    title: '🥶 Nízká teplota',
                    body: `Teplota ${Math.round(temp)}°C - zvažte práci venku`,
                    icon: '🥶',
                    tag: checkKey + '-cold'
                });
                this.lastCheck[checkKey] = Date.now();
            }
            
            // Heat warning
            if (this.settings.weatherAlerts.heatWarning && temp > 30) {
                this.sendNotification({
                    title: '🥵 Vysoká teplota',
                    body: `Teplota ${Math.round(temp)}°C - dbejte na pitný režim`,
                    icon: '🥵',
                    tag: checkKey + '-heat'
                });
                this.lastCheck[checkKey] = Date.now();
            }
        } catch (e) {
            console.error('Error checking weather:', e);
        }
    }
    
    async checkLowStock() {
        try {
            const response = await fetch('/api/warehouse/items?low_stock=1');
            const items = await response.json();
            
            if (!items || items.length === 0) return;
            
            const checkKey = `lowstock-${new Date().toDateString()}`;
            if (this.lastCheck[checkKey]) return;
            
            this.sendNotification({
                title: '📦 Nízké zásoby',
                body: `${items.length} položek má nízké zásoby`,
                icon: '📦',
                tag: checkKey,
                data: { url: '/warehouse' }
            });
            
            this.lastCheck[checkKey] = Date.now();
        } catch (e) {
            console.error('Error checking low stock:', e);
        }
    }
    
    checkDailySummary() {
        const now = new Date();
        const [targetH, targetM] = this.settings.dailySummary.time.split(':').map(Number);
        const currentH = now.getHours();
        const currentM = now.getMinutes();
        
        // Check if it's within 5 minutes of target time
        if (currentH === targetH && currentM >= targetM && currentM < targetM + 5) {
            const checkKey = `summary-${now.toDateString()}`;
            if (this.lastCheck[checkKey]) return;
            
            this.generateDailySummary();
            this.lastCheck[checkKey] = Date.now();
        }
    }
    
    async generateDailySummary() {
        try {
            const [tasksRes, jobsRes] = await Promise.all([
                fetch('/api/tasks').then(r => r.json()),
                fetch('/api/jobs').then(r => r.json())
            ]);
            
            const tasks = Array.isArray(tasksRes) ? tasksRes : (tasksRes.tasks || []);
            const jobs = Array.isArray(jobsRes) ? jobsRes : (jobsRes.jobs || []);
            
            const today = new Date().toISOString().split('T')[0];
            const todayTasks = tasks.filter(t => t.deadline === today && t.status !== 'done');
            const urgentTasks = tasks.filter(t => t.priority === 'urgent' && t.status !== 'done');
            const activeJobs = jobs.filter(j => j.status === 'active').length;
            
            let body = `${todayTasks.length} úkolů na dnes`;
            if (urgentTasks.length > 0) {
                body += `, ${urgentTasks.length} urgentních`;
            }
            body += `. ${activeJobs} aktivních zakázek.`;
            
            this.sendNotification({
                title: '📋 Denní přehled',
                body: body,
                icon: '📋',
                tag: 'daily-summary',
                data: { url: '/' }
            });
        } catch (e) {
            console.error('Error generating daily summary:', e);
        }
    }
    
    sendNotification({ title, body, icon, tag, urgent, data }) {
        // In-app notification
        if (typeof showNotification === 'function') {
            showNotification(body, urgent ? 'warning' : 'info');
        }
        
        // Browser notification
        if (this.settings.pushEnabled && Notification.permission === 'granted') {
            const notification = new Notification(title, {
                body: body,
                icon: '/logo.jpg',
                badge: '/logo.jpg',
                tag: tag,
                requireInteraction: urgent,
                silent: !this.settings.sound
            });
            
            notification.onclick = () => {
                window.focus();
                if (data?.url) {
                    window.location.href = data.url;
                }
                notification.close();
            };
        }
        
        // Play sound
        if (this.settings.sound) {
            this.playNotificationSound(urgent);
        }
    }
    
    playNotificationSound(urgent = false) {
        try {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            const oscillator = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(this.audioContext.destination);
            
            oscillator.frequency.value = urgent ? 880 : 440;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);
            
            oscillator.start();
            oscillator.stop(this.audioContext.currentTime + 0.3);
        } catch (e) {
            console.warn('Could not play notification sound:', e);
        }
    }
    
    // Settings UI
    showSettings() {
        const modal = document.createElement('div');
        modal.className = 'smart-notifications-modal';
        modal.innerHTML = `
            <div class="sn-modal-content">
                <div class="sn-modal-header">
                    <h3>🔔 Nastavení notifikací</h3>
                    <button class="sn-close" onclick="this.closest('.smart-notifications-modal').remove()">&times;</button>
                </div>
                <div class="sn-modal-body">
                    <div class="sn-section">
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-enabled" ${this.settings.enabled ? 'checked' : ''}>
                            <span class="sn-toggle-label">Notifikace povoleny</span>
                        </label>
                    </div>
                    
                    <div class="sn-section">
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-push" ${this.settings.pushEnabled ? 'checked' : ''}>
                            <span class="sn-toggle-label">Push notifikace (prohlížeč)</span>
                        </label>
                        ${Notification.permission === 'denied' ? '<p class="sn-warning">Push notifikace jsou v prohlížeči zakázány</p>' : ''}
                    </div>
                    
                    <div class="sn-section">
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-sound" ${this.settings.sound ? 'checked' : ''}>
                            <span class="sn-toggle-label">Zvuk notifikací</span>
                        </label>
                    </div>
                    
                    <div class="sn-divider"></div>
                    
                    <h4>⏰ Připomínky termínů</h4>
                    <div class="sn-section">
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-deadline-24h" ${this.settings.deadlineReminders.includes(24) ? 'checked' : ''}>
                            <span class="sn-toggle-label">24 hodin předem</span>
                        </label>
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-deadline-2h" ${this.settings.deadlineReminders.includes(2) ? 'checked' : ''}>
                            <span class="sn-toggle-label">2 hodiny předem</span>
                        </label>
                    </div>
                    
                    <div class="sn-divider"></div>
                    
                    <h4>🌤️ Upozornění na počasí</h4>
                    <div class="sn-section">
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-weather" ${this.settings.weatherAlerts.enabled ? 'checked' : ''}>
                            <span class="sn-toggle-label">Počasí celkem</span>
                        </label>
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-rain" ${this.settings.weatherAlerts.rainWarning ? 'checked' : ''}>
                            <span class="sn-toggle-label">Varování před deštěm</span>
                        </label>
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-cold" ${this.settings.weatherAlerts.coldWarning ? 'checked' : ''}>
                            <span class="sn-toggle-label">Varování před chladem (&lt;5°C)</span>
                        </label>
                    </div>
                    
                    <div class="sn-divider"></div>
                    
                    <h4>📋 Denní přehled</h4>
                    <div class="sn-section">
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-summary" ${this.settings.dailySummary.enabled ? 'checked' : ''}>
                            <span class="sn-toggle-label">Denní shrnutí</span>
                        </label>
                        <div class="sn-time-input">
                            <label>Čas:</label>
                            <input type="time" id="sn-summary-time" value="${this.settings.dailySummary.time}">
                        </div>
                    </div>
                    
                    <div class="sn-divider"></div>
                    
                    <h4>🌙 Tichý režim</h4>
                    <div class="sn-section">
                        <label class="sn-toggle">
                            <input type="checkbox" id="sn-quiet" ${this.settings.quietHours.enabled ? 'checked' : ''}>
                            <span class="sn-toggle-label">Tichý režim</span>
                        </label>
                        <div class="sn-time-range">
                            <input type="time" id="sn-quiet-start" value="${this.settings.quietHours.start}">
                            <span>-</span>
                            <input type="time" id="sn-quiet-end" value="${this.settings.quietHours.end}">
                        </div>
                    </div>
                </div>
                <div class="sn-modal-footer">
                    <button class="sn-btn sn-btn-secondary" onclick="this.closest('.smart-notifications-modal').remove()">Zrušit</button>
                    <button class="sn-btn sn-btn-primary" onclick="smartNotifications.saveFromModal()">Uložit</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Fade in
        requestAnimationFrame(() => modal.classList.add('active'));
    }
    
    saveFromModal() {
        this.settings.enabled = document.getElementById('sn-enabled').checked;
        this.settings.pushEnabled = document.getElementById('sn-push').checked;
        this.settings.sound = document.getElementById('sn-sound').checked;
        
        // Deadline reminders
        this.settings.deadlineReminders = [];
        if (document.getElementById('sn-deadline-24h').checked) this.settings.deadlineReminders.push(24);
        if (document.getElementById('sn-deadline-2h').checked) this.settings.deadlineReminders.push(2);
        
        // Weather
        this.settings.weatherAlerts.enabled = document.getElementById('sn-weather').checked;
        this.settings.weatherAlerts.rainWarning = document.getElementById('sn-rain').checked;
        this.settings.weatherAlerts.coldWarning = document.getElementById('sn-cold').checked;
        
        // Daily summary
        this.settings.dailySummary.enabled = document.getElementById('sn-summary').checked;
        this.settings.dailySummary.time = document.getElementById('sn-summary-time').value;
        
        // Quiet hours
        this.settings.quietHours.enabled = document.getElementById('sn-quiet').checked;
        this.settings.quietHours.start = document.getElementById('sn-quiet-start').value;
        this.settings.quietHours.end = document.getElementById('sn-quiet-end').value;
        
        this.saveSettings();
        
        // Request push permission if enabled
        if (this.settings.pushEnabled) {
            this.requestPushPermission();
        }
        
        // Close modal
        document.querySelector('.smart-notifications-modal')?.remove();
        
        // Show confirmation
        if (typeof showNotification === 'function') {
            showNotification('Nastavení notifikací uloženo', 'success');
        }
    }
}

// Inject CSS for settings modal
const snStyles = document.createElement('style');
snStyles.textContent = `
    .smart-notifications-modal {
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
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .smart-notifications-modal.active {
        opacity: 1;
    }
    
    .sn-modal-content {
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 16px;
        width: 90%;
        max-width: 480px;
        max-height: 80vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
    }
    
    .sn-modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 24px;
        border-bottom: 1px solid var(--border-primary, #2d3748);
    }
    
    .sn-modal-header h3 {
        margin: 0;
        font-size: 18px;
    }
    
    .sn-close {
        background: none;
        border: none;
        color: var(--text-secondary, #9ca8b3);
        font-size: 28px;
        cursor: pointer;
        line-height: 1;
    }
    
    .sn-modal-body {
        padding: 24px;
        overflow-y: auto;
    }
    
    .sn-modal-body h4 {
        margin: 0 0 12px 0;
        font-size: 14px;
        color: var(--text-secondary, #9ca8b3);
    }
    
    .sn-section {
        margin-bottom: 16px;
    }
    
    .sn-toggle {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 0;
        cursor: pointer;
    }
    
    .sn-toggle input[type="checkbox"] {
        width: 20px;
        height: 20px;
        accent-color: var(--mint, #4ade80);
    }
    
    .sn-toggle-label {
        font-size: 14px;
    }
    
    .sn-time-input, .sn-time-range {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 8px;
        padding-left: 32px;
    }
    
    .sn-time-input input, .sn-time-range input {
        padding: 8px 12px;
        background: var(--bg-elevated, #242a33);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 8px;
        color: var(--text-primary, #e8eef2);
    }
    
    .sn-divider {
        height: 1px;
        background: var(--border-primary, #2d3748);
        margin: 20px 0;
    }
    
    .sn-warning {
        color: #ef4444;
        font-size: 12px;
        margin-top: 4px;
        padding-left: 32px;
    }
    
    .sn-modal-footer {
        display: flex;
        justify-content: flex-end;
        gap: 12px;
        padding: 16px 24px;
        border-top: 1px solid var(--border-primary, #2d3748);
    }
    
    .sn-btn {
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .sn-btn-secondary {
        background: transparent;
        border: 1px solid var(--border-primary, #2d3748);
        color: var(--text-secondary, #9ca8b3);
    }
    
    .sn-btn-secondary:hover {
        border-color: var(--text-secondary, #9ca8b3);
    }
    
    .sn-btn-primary {
        background: var(--mint, #4ade80);
        border: none;
        color: #0a0e11;
    }
    
    .sn-btn-primary:hover {
        background: #7bc47e;
    }
`;
document.head.appendChild(snStyles);

// Global instance
window.smartNotifications = new SmartNotifications();

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => smartNotifications.init());
} else {
    smartNotifications.init();
}
