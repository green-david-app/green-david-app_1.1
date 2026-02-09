/**
 * AI OPERATOR DRAWER - Globální postranní panel
 * =============================================
 * AI Operátor je vrstva, ne stránka.
 * Zobrazuje se jako drawer přes aktuální obsah.
 * 
 * Principy:
 * - Viditelný všude (Global Operator Button v headeru)
 * - Neodchází uživatel ze své práce
 * - Offline-capable (pravidlové insighty)
 * - Drafty k potvrzení
 */

class AIOperatorDrawer {
    constructor() {
        this.isOpen = false;
        this.activeTab = 'critical';
        this.activeFilter = null;
        this.insights = [];
        this.drafts = [];
        this.isOffline = !navigator.onLine;
        
        this.init();
    }

    init() {
        this.injectStyles();
        this.injectHTML();
        this.bindEvents();
        this.addHeaderButton();
        this.loadData();
        
        // Offline detection
        window.addEventListener('online', () => {
            this.isOffline = false;
            this.updateOfflineIndicator();
            this.loadData();
        });
        window.addEventListener('offline', () => {
            this.isOffline = true;
            this.updateOfflineIndicator();
        });
        
        // Refresh every 60s
        setInterval(() => this.loadData(), 60000);
    }

    // SVG ikony
    get icons() {
        return {
            brain: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2a7 7 0 0 0-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 0 0 2 2h4a2 2 0 0 0 2-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 0 0-7-7Z"/>
                <path d="M8 21h8"/>
                <path d="M12 17v4"/>
            </svg>`,
            close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6L6 18M6 6l12 12"/></svg>`,
            alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
            check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`,
            clock: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
            package: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16.5 9.4l-9-5.19"/><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>`,
            users: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>`,
            briefcase: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>`,
            calendar: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`,
            cloud: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z"/></svg>`,
            offline: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 1l22 22"/><path d="M16.72 11.06A10.94 10.94 0 0119 12.55"/><path d="M5 12.55a10.94 10.94 0 015.17-2.39"/><path d="M10.71 5.05A16 16 0 0122.58 9"/><path d="M1.42 9a15.91 15.91 0 014.7-2.88"/><path d="M8.53 16.11a6 6 0 016.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>`,
            zap: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
            eye: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`,
            bellOff: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M13.73 21a2 2 0 01-3.46 0"/><path d="M18.63 13A17.89 17.89 0 0118 8"/><path d="M6.26 6.26A5.86 5.86 0 006 8c0 7-3 9-3 9h14"/><path d="M18 8a6 6 0 00-9.33-5"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`,
            fileText: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`,
            trash: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>`,
            play: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>`
        };
    }

    injectStyles() {
        if (document.getElementById('ai-operator-drawer-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'ai-operator-drawer-styles';
        style.textContent = `
            /* Global Operator Button in Header */
            .ai-operator-btn {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                background: linear-gradient(135deg, #1f2940 0%, #16213e 100%);
                border: 1px solid #2d3748;
                border-radius: 8px;
                color: #4ade80;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 13px;
                font-weight: 500;
            }
            .ai-operator-btn:hover {
                background: linear-gradient(135deg, #2d3748 0%, #1f2940 100%);
                border-color: #4ade80;
            }
            .ai-operator-btn svg {
                width: 18px;
                height: 18px;
            }
            .ai-operator-btn .badge {
                display: flex;
                align-items: center;
                gap: 4px;
                font-size: 11px;
            }
            .ai-operator-btn .badge-critical {
                background: rgba(248, 113, 113, 0.2);
                color: #f87171;
                padding: 2px 6px;
                border-radius: 10px;
            }
            .ai-operator-btn .badge-warn {
                background: rgba(251, 191, 36, 0.2);
                color: #fbbf24;
                padding: 2px 6px;
                border-radius: 10px;
            }
            .ai-operator-btn .offline-indicator {
                color: #f87171;
                font-size: 10px;
            }

            /* Drawer Overlay */
            .ai-operator-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.5);
                z-index: 9998;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
            }
            .ai-operator-overlay.open {
                opacity: 1;
                visibility: visible;
            }

            /* Drawer Panel */
            .ai-operator-drawer {
                position: fixed;
                top: 0;
                right: -420px;
                width: 420px;
                max-width: 100vw;
                height: 100vh;
                background: #0f1729;
                border-left: 1px solid #2d3748;
                z-index: 9999;
                display: flex;
                flex-direction: column;
                transition: right 0.3s ease;
                box-shadow: -4px 0 20px rgba(0, 0, 0, 0.3);
            }
            .ai-operator-drawer.open {
                right: 0;
            }

            /* Drawer Header */
            .ai-drawer-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 16px 20px;
                border-bottom: 1px solid #2d3748;
                background: linear-gradient(135deg, #1f2940 0%, #16213e 100%);
            }
            .ai-drawer-title {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .ai-drawer-title svg {
                width: 24px;
                height: 24px;
                color: #4ade80;
            }
            .ai-drawer-title h2 {
                margin: 0;
                font-size: 18px;
                color: #fff;
                font-weight: 600;
            }
            .ai-drawer-title span {
                font-size: 12px;
                color: #888;
                display: block;
            }
            .ai-drawer-actions {
                display: flex;
                gap: 8px;
            }
            .ai-drawer-btn {
                padding: 8px 12px;
                border-radius: 6px;
                border: 1px solid #2d3748;
                background: #16213e;
                color: #fff;
                cursor: pointer;
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 4px;
                transition: all 0.2s;
            }
            .ai-drawer-btn:hover {
                background: #1f2940;
                border-color: #4ade80;
            }
            .ai-drawer-btn svg {
                width: 14px;
                height: 14px;
            }
            .ai-drawer-close {
                padding: 8px;
                border: none;
                background: transparent;
                color: #888;
                cursor: pointer;
                border-radius: 6px;
            }
            .ai-drawer-close:hover {
                background: #1f2940;
                color: #fff;
            }
            .ai-drawer-close svg {
                width: 20px;
                height: 20px;
            }

            /* Offline Banner */
            .ai-offline-banner {
                display: none;
                padding: 8px 16px;
                background: rgba(248, 113, 113, 0.1);
                border-bottom: 1px solid rgba(248, 113, 113, 0.3);
                color: #f87171;
                font-size: 12px;
                align-items: center;
                gap: 8px;
            }
            .ai-offline-banner.show {
                display: flex;
            }
            .ai-offline-banner svg {
                width: 16px;
                height: 16px;
            }

            /* Tabs */
            .ai-drawer-tabs {
                display: flex;
                padding: 12px 16px;
                gap: 8px;
                border-bottom: 1px solid #2d3748;
            }
            .ai-drawer-tab {
                flex: 1;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid transparent;
                background: transparent;
                color: #888;
                cursor: pointer;
                font-size: 13px;
                font-weight: 500;
                text-align: center;
                transition: all 0.2s;
            }
            .ai-drawer-tab:hover {
                background: #16213e;
            }
            .ai-drawer-tab.active {
                background: #16213e;
                border-color: #2d3748;
                color: #fff;
            }
            .ai-drawer-tab.critical.active {
                border-color: #f87171;
                color: #f87171;
            }
            .ai-drawer-tab.warn.active {
                border-color: #fbbf24;
                color: #fbbf24;
            }
            .ai-drawer-tab.info.active {
                border-color: #60a5fa;
                color: #60a5fa;
            }
            .ai-drawer-tab .tab-count {
                display: inline-block;
                margin-left: 4px;
                padding: 2px 6px;
                border-radius: 10px;
                font-size: 11px;
                background: rgba(255,255,255,0.1);
            }

            /* Filters */
            .ai-drawer-filters {
                display: flex;
                gap: 6px;
                padding: 12px 16px;
                overflow-x: auto;
                border-bottom: 1px solid #2d3748;
            }
            .ai-filter-chip {
                padding: 6px 12px;
                border-radius: 16px;
                border: 1px solid #2d3748;
                background: transparent;
                color: #888;
                cursor: pointer;
                font-size: 12px;
                white-space: nowrap;
                transition: all 0.2s;
            }
            .ai-filter-chip:hover {
                background: #16213e;
            }
            .ai-filter-chip.active {
                background: #4ade80;
                border-color: #4ade80;
                color: #0f1729;
            }

            /* Content */
            .ai-drawer-content {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
            }

            /* Insight Card */
            .ai-insight-card {
                background: #16213e;
                border-radius: 12px;
                border-left: 4px solid #2d3748;
                margin-bottom: 12px;
                overflow: hidden;
            }
            .ai-insight-card.critical {
                border-left-color: #f87171;
                background: rgba(248, 113, 113, 0.08);
            }
            .ai-insight-card.warn {
                border-left-color: #fbbf24;
                background: rgba(251, 191, 36, 0.08);
            }
            .ai-insight-card.info {
                border-left-color: #60a5fa;
            }
            .ai-insight-header {
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                padding: 14px;
                cursor: pointer;
            }
            .ai-insight-title {
                font-size: 14px;
                font-weight: 500;
                color: #fff;
                margin-bottom: 4px;
            }
            .ai-insight-meta {
                display: flex;
                gap: 8px;
                align-items: center;
                flex-wrap: wrap;
            }
            .ai-insight-impact {
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 4px;
                background: rgba(255,255,255,0.1);
                color: #aaa;
            }
            .ai-insight-confidence {
                font-size: 11px;
                color: #666;
            }
            .ai-insight-confidence.high { color: #4ade80; }
            .ai-insight-confidence.medium { color: #fbbf24; }
            .ai-insight-confidence.low { color: #f87171; }
            .ai-insight-body {
                padding: 0 14px 14px;
                display: none;
            }
            .ai-insight-card.expanded .ai-insight-body {
                display: block;
            }
            .ai-insight-evidence {
                font-size: 13px;
                color: #aaa;
                margin-bottom: 12px;
            }
            .ai-insight-evidence a {
                color: #60a5fa;
                text-decoration: none;
            }
            .ai-insight-cta {
                display: flex;
                gap: 8px;
                flex-wrap: wrap;
            }
            .ai-cta-btn {
                padding: 8px 14px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                font-size: 12px;
                font-weight: 500;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            .ai-cta-btn svg {
                width: 14px;
                height: 14px;
            }
            .ai-cta-btn.primary {
                background: #4ade80;
                color: #0f1729;
            }
            .ai-cta-btn.primary:hover {
                background: #22c55e;
            }
            .ai-cta-btn.secondary {
                background: #1f2940;
                color: #fff;
                border: 1px solid #2d3748;
            }
            .ai-cta-btn.secondary:hover {
                border-color: #4ade80;
            }
            .ai-cta-btn.ghost {
                background: transparent;
                color: #888;
            }
            .ai-cta-btn.ghost:hover {
                color: #fff;
            }

            /* Draft Queue */
            .ai-draft-queue {
                padding: 12px 16px;
                border-top: 1px solid #2d3748;
                background: #16213e;
            }
            .ai-draft-queue-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: pointer;
            }
            .ai-draft-queue-title {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #fff;
                font-size: 14px;
                font-weight: 500;
            }
            .ai-draft-queue-title svg {
                width: 18px;
                height: 18px;
                color: #fbbf24;
            }
            .ai-draft-count {
                background: #fbbf24;
                color: #0f1729;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
            }
            .ai-draft-list {
                margin-top: 12px;
                display: none;
            }
            .ai-draft-queue.expanded .ai-draft-list {
                display: block;
            }
            .ai-draft-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 12px;
                background: #0f1729;
                border-radius: 8px;
                margin-bottom: 8px;
            }
            .ai-draft-item:last-child {
                margin-bottom: 0;
            }
            .ai-draft-info {
                flex: 1;
            }
            .ai-draft-title {
                font-size: 13px;
                color: #fff;
            }
            .ai-draft-desc {
                font-size: 11px;
                color: #888;
                margin-top: 2px;
            }
            .ai-draft-actions {
                display: flex;
                gap: 6px;
            }
            .ai-draft-actions button {
                padding: 6px 10px;
                border-radius: 4px;
                border: none;
                cursor: pointer;
                font-size: 11px;
            }
            .ai-draft-approve {
                background: #4ade80;
                color: #0f1729;
            }
            .ai-draft-reject {
                background: #f87171;
                color: #fff;
            }

            /* Empty State */
            .ai-empty-state {
                text-align: center;
                padding: 40px 20px;
                color: #666;
            }
            .ai-empty-state svg {
                width: 48px;
                height: 48px;
                margin-bottom: 16px;
                color: #4ade80;
            }
            .ai-empty-state h3 {
                color: #fff;
                margin: 0 0 8px;
                font-size: 16px;
            }

            /* Mobile */
            @media (max-width: 480px) {
                .ai-operator-drawer {
                    width: 100vw;
                    right: -100vw;
                }
                .ai-operator-btn .badge span:last-child {
                    display: none;
                }
            }
        `;
        document.head.appendChild(style);
    }

    injectHTML() {
        // Overlay
        const overlay = document.createElement('div');
        overlay.className = 'ai-operator-overlay';
        overlay.id = 'ai-operator-overlay';
        overlay.addEventListener('click', () => this.close());
        document.body.appendChild(overlay);

        // Drawer
        const drawer = document.createElement('div');
        drawer.className = 'ai-operator-drawer';
        drawer.id = 'ai-operator-drawer';
        drawer.innerHTML = `
            <div class="ai-drawer-header">
                <div class="ai-drawer-title">
                    ${this.icons.brain}
                    <div>
                        <h2>AI Operátor</h2>
                        <span>Digitální mozek firmy</span>
                    </div>
                </div>
                <div class="ai-drawer-actions">
                    <button class="ai-drawer-btn" onclick="aiOperatorDrawer.showDigest()" title="Denní přehled">
                        ${this.icons.fileText}
                        <span>Digest</span>
                    </button>
                    <button class="ai-drawer-close" onclick="aiOperatorDrawer.close()">
                        ${this.icons.close}
                    </button>
                </div>
            </div>
            
            <div class="ai-offline-banner" id="ai-offline-banner">
                ${this.icons.offline}
                <span>Offline režim – lokální doporučení</span>
            </div>
            
            <div class="ai-drawer-tabs">
                <button class="ai-drawer-tab critical active" data-tab="critical" onclick="aiOperatorDrawer.setTab('critical')">
                    Kritické <span class="tab-count" id="critical-count">0</span>
                </button>
                <button class="ai-drawer-tab warn" data-tab="warn" onclick="aiOperatorDrawer.setTab('warn')">
                    Varování <span class="tab-count" id="warn-count">0</span>
                </button>
                <button class="ai-drawer-tab info" data-tab="info" onclick="aiOperatorDrawer.setTab('info')">
                    Doporučení <span class="tab-count" id="info-count">0</span>
                </button>
            </div>
            
            <div class="ai-drawer-filters">
                <button class="ai-filter-chip active" data-filter="" onclick="aiOperatorDrawer.setFilter('')">Vše</button>
                <button class="ai-filter-chip" data-filter="jobs" onclick="aiOperatorDrawer.setFilter('jobs')">
                    ${this.icons.briefcase} Zakázky
                </button>
                <button class="ai-filter-chip" data-filter="tasks" onclick="aiOperatorDrawer.setFilter('tasks')">
                    ${this.icons.check} Úkoly
                </button>
                <button class="ai-filter-chip" data-filter="team" onclick="aiOperatorDrawer.setFilter('team')">
                    ${this.icons.users} Tým
                </button>
                <button class="ai-filter-chip" data-filter="warehouse" onclick="aiOperatorDrawer.setFilter('warehouse')">
                    ${this.icons.package} Sklad
                </button>
                <button class="ai-filter-chip" data-filter="weather" onclick="aiOperatorDrawer.setFilter('weather')">
                    ${this.icons.cloud} Počasí
                </button>
            </div>
            
            <div class="ai-drawer-content" id="ai-drawer-content">
                <div class="ai-empty-state">
                    ${this.icons.check}
                    <h3>Načítám data...</h3>
                    <p>Chvilku strpení</p>
                </div>
            </div>
            
            <div class="ai-draft-queue" id="ai-draft-queue" style="display: none;">
                <div class="ai-draft-queue-header" onclick="aiOperatorDrawer.toggleDraftQueue()">
                    <div class="ai-draft-queue-title">
                        ${this.icons.zap}
                        <span>Drafty k potvrzení</span>
                    </div>
                    <span class="ai-draft-count" id="ai-draft-count">0</span>
                </div>
                <div class="ai-draft-list" id="ai-draft-list"></div>
            </div>
        `;
        document.body.appendChild(drawer);
    }

    addHeaderButton() {
        // Použij existující AI ikonu z app-header.js
        const existingBtn = document.getElementById('app-header-ai-toggle');
        if (existingBtn) {
            // Jen přidej click listener, nevytvářej nový element
            existingBtn.addEventListener('click', () => this.toggle());
            return;
        }
        
        // Fallback: pokud header ještě neexistuje
        setTimeout(() => this.addHeaderButton(), 100);
    }

    bindEvents() {
        // ESC zavře drawer
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        this.isOpen = true;
        document.getElementById('ai-operator-overlay').classList.add('open');
        document.getElementById('ai-operator-drawer').classList.add('open');
        document.body.style.overflow = 'hidden';
        this.loadData();
    }

    close() {
        this.isOpen = false;
        document.getElementById('ai-operator-overlay').classList.remove('open');
        document.getElementById('ai-operator-drawer').classList.remove('open');
        document.body.style.overflow = '';
    }

    setTab(tab) {
        this.activeTab = tab;
        
        // Update tab buttons
        document.querySelectorAll('.ai-drawer-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tab);
        });
        
        this.renderInsights();
    }

    setFilter(filter) {
        this.activeFilter = filter || null;
        
        // Update filter chips
        document.querySelectorAll('.ai-filter-chip').forEach(f => {
            f.classList.toggle('active', (f.dataset.filter || '') === (filter || ''));
        });
        
        this.renderInsights();
    }

    updateOfflineIndicator() {
        const indicator = document.getElementById('ai-offline-indicator');
        const banner = document.getElementById('ai-offline-banner');
        
        if (indicator) {
            indicator.style.display = this.isOffline ? 'inline' : 'none';
        }
        if (banner) {
            banner.classList.toggle('show', this.isOffline);
        }
    }

    async loadData() {
        try {
            // Fetch complete brain analysis
            const response = await fetch('/api/ai/brain/analysis');
            const data = await response.json();
            
            // Transform insights to drawer format
            this.insights = [];
            
            if (data.insights) {
                data.insights.forEach(insight => {
                    this.insights.push({
                        id: insight.key,
                        severity: insight.severity.toLowerCase(),
                        title: insight.title,
                        evidence: insight.summary,
                        impact: insight.category,
                        confidence: insight.confidence.toLowerCase(),
                        category: insight.category,
                        entity: insight.entity_type,
                        entityId: insight.entity_id,
                        actions: insight.actions
                    });
                });
            }
            
            // Store predictions and comparisons for digest
            this.predictions = data.predictions || [];
            this.comparisons = data.comparisons || [];
            this.stats = data.stats || {};
            
            this.updateBadges();
            this.renderInsights();
            this.loadDrafts();
            
        } catch (error) {
            console.error('AI Operator data load error:', error);
            // Fallback to old API
            this.loadDataLegacy();
        }
    }

    async loadDataLegacy() {
        try {
            // Fallback to old dashboard API
            const response = await fetch('/api/ai/dashboard');
            const data = await response.json();
            
            this.insights = [];
            
            if (data.warnings) {
                data.warnings.forEach(w => {
                    this.insights.push({
                        id: w.id,
                        severity: w.severity === 'critical' ? 'critical' : 'warn',
                        title: w.title,
                        evidence: w.detail,
                        impact: w.type,
                        confidence: 'high',
                        category: this.categorizeInsight(w.type),
                        entity: w.entity,
                        entityId: w.entity_id,
                        action: w.action
                    });
                });
            }
            
            if (data.recommendations) {
                data.recommendations.forEach(r => {
                    this.insights.push({
                        id: r.id,
                        severity: 'info',
                        title: r.title,
                        evidence: r.detail,
                        impact: r.type,
                        confidence: 'medium',
                        category: this.categorizeInsight(r.type),
                        entity: r.entity,
                        entityId: r.entity_id,
                        action: r.action
                    });
                });
            }
            
            this.updateBadges();
            this.renderInsights();
            this.loadDrafts();
            
        } catch (error) {
            console.error('Legacy API also failed:', error);
            this.renderOfflineState();
        }
    }

    categorizeInsight(type) {
        const mapping = {
            'budget_overrun': 'jobs',
            'overwork': 'team',
            'low_stock': 'warehouse',
            'inactive_job': 'jobs',
            'delay': 'jobs',
            'unassigned_task': 'tasks',
            'weather': 'weather',
            'workload': 'team',
            'material': 'warehouse',
            'completion': 'jobs'
        };
        return mapping[type] || 'jobs';
    }

    updateBadges() {
        const criticalCount = this.insights.filter(i => i.severity === 'critical').length;
        const warnCount = this.insights.filter(i => i.severity === 'warn').length;
        const infoCount = this.insights.filter(i => i.severity === 'info').length;
        
        // Header badge
        const criticalBadge = document.getElementById('ai-badge-critical');
        const warnBadge = document.getElementById('ai-badge-warn');
        
        if (criticalBadge) {
            criticalBadge.textContent = criticalCount;
            criticalBadge.style.display = criticalCount > 0 ? 'inline' : 'none';
        }
        if (warnBadge) {
            warnBadge.textContent = warnCount;
            warnBadge.style.display = warnCount > 0 ? 'inline' : 'none';
        }
        
        // Tab counts
        document.getElementById('critical-count').textContent = criticalCount;
        document.getElementById('warn-count').textContent = warnCount;
        document.getElementById('info-count').textContent = infoCount;
    }

    renderInsights() {
        const container = document.getElementById('ai-drawer-content');
        
        // Filter insights
        let filtered = this.insights.filter(i => {
            // Tab filter
            if (this.activeTab === 'critical' && i.severity !== 'critical') return false;
            if (this.activeTab === 'warn' && i.severity !== 'warn') return false;
            if (this.activeTab === 'info' && i.severity !== 'info') return false;
            
            // Category filter
            if (this.activeFilter && i.category !== this.activeFilter) return false;
            
            return true;
        });
        
        if (filtered.length === 0) {
            container.innerHTML = `
                <div class="ai-empty-state">
                    ${this.icons.check}
                    <h3>Vše v pořádku!</h3>
                    <p>Žádná upozornění v této kategorii</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = filtered.map(insight => this.renderInsightCard(insight)).join('');
    }

    renderInsightCard(insight) {
        const confidenceClass = insight.confidence || 'medium';
        
        // Build action buttons from insight.actions array
        let actionButtons = '';
        if (insight.actions && insight.actions.length > 0) {
            insight.actions.forEach(action => {
                if (action.type === 'link') {
                    actionButtons += `
                        <button class="ai-cta-btn primary" onclick="aiOperatorDrawer.executeAction('${insight.id}', 'link', '${action.url || ''}')">
                            ${this.icons.eye}
                            ${action.label || 'Zobrazit'}
                        </button>
                    `;
                } else if (action.type === 'draft') {
                    actionButtons += `
                        <button class="ai-cta-btn secondary" onclick="aiOperatorDrawer.createDraftAction('${insight.id}', '${action.action || 'review'}', '${insight.title}')">
                            ${this.icons.zap}
                            ${action.label || 'Akce'}
                        </button>
                    `;
                }
            });
        }
        
        // Fallback for old format
        if (!actionButtons && insight.action) {
            actionButtons = `
                <button class="ai-cta-btn primary" onclick="aiOperatorDrawer.executeAction('${insight.id}', '${insight.action.type}', '${insight.action.url || ''}')">
                    ${this.icons.play}
                    ${insight.action.label || 'Akce'}
                </button>
            `;
        }
        
        return `
            <div class="ai-insight-card ${insight.severity}" data-id="${insight.id}">
                <div class="ai-insight-header" onclick="aiOperatorDrawer.toggleInsight('${insight.id}')">
                    <div>
                        <div class="ai-insight-title">${this.escapeHtml(insight.title)}</div>
                        <div class="ai-insight-meta">
                            <span class="ai-insight-impact">${insight.impact || insight.category}</span>
                            <span class="ai-insight-confidence ${confidenceClass}">${confidenceClass.toUpperCase()}</span>
                        </div>
                    </div>
                </div>
                <div class="ai-insight-body">
                    <div class="ai-insight-evidence">${this.escapeHtml(insight.evidence || '')}</div>
                    <div class="ai-insight-cta">
                        ${actionButtons}
                        <button class="ai-cta-btn ghost" onclick="aiOperatorDrawer.snoozeInsight('${insight.id}')">
                            ${this.icons.clock}
                            Odložit
                        </button>
                        <button class="ai-cta-btn ghost" onclick="aiOperatorDrawer.dismissInsight('${insight.id}')">
                            ${this.icons.bellOff}
                            Zavřít
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    toggleInsight(id) {
        const card = document.querySelector(`.ai-insight-card[data-id="${id}"]`);
        if (card) {
            card.classList.toggle('expanded');
        }
    }

    executeAction(id, type, url) {
        if (type === 'link' && url) {
            this.close();
            window.location.href = url;
        }
    }

    async createDraft(insightId) {
        const insight = this.insights.find(i => i.id === insightId);
        if (!insight) return;
        
        try {
            const response = await fetch('/api/ai/drafts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    insight_id: insightId,
                    type: 'review',
                    title: insight.title,
                    entity: insight.entity,
                    entity_id: insight.entityId
                })
            });
            
            if (response.ok) {
                this.showToast('Draft vytvořen!', 'success');
                this.loadDrafts();
                
                // Log to learning layer
                this.logDecision(insightId, 'create_draft', 'pending');
            }
        } catch (error) {
            console.error('Create draft error:', error);
            this.showToast('Nepodařilo se vytvořit draft', 'error');
        }
    }

    async createDraftAction(insightId, actionType, title) {
        // Vytvoří draft akci specifického typu
        try {
            const response = await fetch('/api/ai/drafts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    insight_id: insightId,
                    type: actionType,
                    title: title,
                    payload: { source: 'drawer', action_type: actionType }
                })
            });
            
            if (response.ok) {
                this.showToast(`Draft "${actionType}" vytvořen!`, 'success');
                this.loadDrafts();
                
                // Log to learning layer
                this.logDecision(insightId, actionType, 'pending');
            }
        } catch (error) {
            console.error('Create draft action error:', error);
            this.showToast('Nepodařilo se vytvořit draft', 'error');
        }
    }

    async logDecision(insightId, action, outcome) {
        // Zaloguj rozhodnutí pro learning layer
        try {
            await fetch('/api/ai/brain/learn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    insight_id: insightId,
                    action: action,
                    outcome: outcome
                })
            });
        } catch (error) {
            debugLog('Learning log failed (non-critical)');
        }
    }

    async snoozeInsight(id) {
        try {
            await fetch(`/api/ai/insight/${id}/snooze`, { method: 'POST' });
            this.showToast('Odloženo na 24h', 'success');
            this.loadData();
        } catch (error) {
            console.error('Snooze error:', error);
        }
    }

    async dismissInsight(id) {
        if (!confirm('Opravdu zavřít toto upozornění?')) return;
        
        try {
            await fetch(`/api/ai/insight/${id}/dismiss`, { method: 'POST' });
            this.showToast('Zavřeno', 'success');
            this.loadData();
        } catch (error) {
            console.error('Dismiss error:', error);
        }
    }

    async loadDrafts() {
        try {
            const response = await fetch('/api/ai/drafts');
            const data = await response.json();
            this.drafts = data.drafts || [];
            this.renderDrafts();
        } catch (error) {
            console.error('Load drafts error:', error);
        }
    }

    renderDrafts() {
        const queue = document.getElementById('ai-draft-queue');
        const list = document.getElementById('ai-draft-list');
        const count = document.getElementById('ai-draft-count');
        
        if (this.drafts.length === 0) {
            queue.style.display = 'none';
            return;
        }
        
        queue.style.display = 'block';
        count.textContent = this.drafts.length;
        
        list.innerHTML = this.drafts.map(draft => `
            <div class="ai-draft-item" data-id="${draft.id}">
                <div class="ai-draft-info">
                    <div class="ai-draft-title">${this.escapeHtml(draft.title)}</div>
                    <div class="ai-draft-desc">${draft.type} • ${this.formatTimeAgo(draft.created_at)}</div>
                </div>
                <div class="ai-draft-actions">
                    <button class="ai-draft-approve" onclick="aiOperatorDrawer.approveDraft(${draft.id})">Schválit</button>
                    <button class="ai-draft-reject" onclick="aiOperatorDrawer.rejectDraft(${draft.id})">Zamítnout</button>
                </div>
            </div>
        `).join('');
    }

    toggleDraftQueue() {
        document.getElementById('ai-draft-queue').classList.toggle('expanded');
    }

    async approveDraft(id) {
        try {
            const response = await fetch(`/api/ai/drafts/${id}/approve`, { method: 'POST' });
            if (response.ok) {
                this.showToast('Draft schválen a proveden!', 'success');
                this.loadDrafts();
                this.loadData();
            }
        } catch (error) {
            console.error('Approve draft error:', error);
        }
    }

    async rejectDraft(id) {
        try {
            await fetch(`/api/ai/drafts/${id}/reject`, { method: 'POST' });
            this.showToast('Draft zamítnut', 'success');
            this.loadDrafts();
        } catch (error) {
            console.error('Reject draft error:', error);
        }
    }

    showDigest() {
        window.location.href = '/ai-operator.html#digest';
        this.close();
    }

    renderOfflineState() {
        const container = document.getElementById('ai-drawer-content');
        container.innerHTML = `
            <div class="ai-empty-state">
                ${this.icons.offline}
                <h3>Offline režim</h3>
                <p>Některé funkce nejsou dostupné bez připojení</p>
            </div>
        `;
    }

    showToast(message, type = 'info') {
        // Use existing toast system if available
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            debugLog(`[${type}] ${message}`);
        }
    }

    formatTimeAgo(dateStr) {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        
        if (diffMins < 1) return 'právě teď';
        if (diffMins < 60) return `před ${diffMins} min`;
        if (diffHours < 24) return `před ${diffHours} hod`;
        return date.toLocaleDateString('cs-CZ');
    }

    escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
}

// Auto-init
let aiOperatorDrawer = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        aiOperatorDrawer = new AIOperatorDrawer();
        window.aiOperatorDrawer = aiOperatorDrawer;
    });
} else {
    aiOperatorDrawer = new AIOperatorDrawer();
    window.aiOperatorDrawer = aiOperatorDrawer;
}
