/**
 * AI OPERATOR DRAWER
 * ==================
 * Globální vrstva AI Operátora - digitální mozek firmy
 * Drawer se otevírá přes aktuální stránku
 */

class AIOperatorDrawer {
  constructor() {
    this.isOpen = false;
    this.insights = [];
    this.drafts = [];
    this.activeFilter = 'all';
    this.activeTab = 'critical';
    this.isOffline = !navigator.onLine;
    
    this.init();
  }

  init() {
    this.injectButton();
    this.injectDrawer();
    this.injectStyles();
    this.bindEvents();
    this.loadInsights();
    this.startPolling();
    this.monitorConnection();
  }

  // SVG ikona - terč/radar styl
  get operatorIcon() {
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <circle cx="12" cy="12" r="6"/>
      <circle cx="12" cy="12" r="2"/>
      <line x1="12" y1="2" x2="12" y2="6"/>
      <line x1="12" y1="18" x2="12" y2="22"/>
      <line x1="2" y1="12" x2="6" y2="12"/>
      <line x1="18" y1="12" x2="22" y2="12"/>
    </svg>`;
  }

  injectButton() {
    // Počkej na header
    const waitForHeader = () => {
      const actions = document.querySelector('.app-header-actions');
      if (!actions) {
        setTimeout(waitForHeader, 100);
        return;
      }

      // Vložit před settings
      const settings = actions.querySelector('.app-header-settings');
      if (actions.querySelector('.ai-operator-btn')) return;

      const btn = document.createElement('button');
      btn.className = 'ai-operator-btn';
      btn.id = 'ai-operator-toggle';
      btn.title = 'AI Operátor';
      btn.innerHTML = `
        ${this.operatorIcon}
        <span class="ai-operator-badge" id="ai-operator-badge" style="display:none;">0</span>
        <span class="ai-operator-offline" id="ai-operator-offline" style="display:none;">⚡</span>
      `;

      if (settings) {
        actions.insertBefore(btn, settings);
      } else {
        actions.appendChild(btn);
      }
    };

    waitForHeader();
  }

  injectDrawer() {
    if (document.getElementById('ai-operator-drawer')) return;

    const drawer = document.createElement('div');
    drawer.id = 'ai-operator-drawer';
    drawer.className = 'ai-drawer';
    drawer.innerHTML = `
      <div class="ai-drawer-overlay" id="ai-drawer-overlay"></div>
      <div class="ai-drawer-panel">
        <div class="ai-drawer-header">
          <div class="ai-drawer-title">
            ${this.operatorIcon}
            <div>
              <h2>AI Operátor</h2>
              <span class="ai-drawer-subtitle">Digitální mozek firmy</span>
            </div>
          </div>
          <div class="ai-drawer-header-actions">
            <button class="ai-drawer-digest-btn" id="ai-digest-btn" title="Ranní digest">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"/>
              </svg>
            </button>
            <button class="ai-drawer-close" id="ai-drawer-close" title="Zavřít">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 6L6 18M6 6l12 12"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="ai-drawer-tabs">
          <button class="ai-tab active" data-tab="critical">
            <span class="ai-tab-dot critical"></span>
            Kritické <span class="ai-tab-count" id="critical-count">0</span>
          </button>
          <button class="ai-tab" data-tab="warning">
            <span class="ai-tab-dot warning"></span>
            Varování <span class="ai-tab-count" id="warning-count">0</span>
          </button>
          <button class="ai-tab" data-tab="info">
            <span class="ai-tab-dot info"></span>
            Doporučení <span class="ai-tab-count" id="info-count">0</span>
          </button>
        </div>

        <div class="ai-drawer-filters">
          <button class="ai-filter active" data-filter="all">Vše</button>
          <button class="ai-filter" data-filter="jobs">Zakázky</button>
          <button class="ai-filter" data-filter="tasks">Úkoly</button>
          <button class="ai-filter" data-filter="team">Tým</button>
          <button class="ai-filter" data-filter="warehouse">Sklad</button>
          <button class="ai-filter" data-filter="timesheets">Výkazy</button>
        </div>

        <div class="ai-drawer-content" id="ai-drawer-content">
          <div class="ai-loading">
            <div class="ai-loading-spinner"></div>
            <span>Načítám insighty...</span>
          </div>
        </div>

        <div class="ai-drawer-drafts" id="ai-drawer-drafts">
          <button class="ai-drafts-toggle" id="ai-drafts-toggle">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
              <rect x="9" y="3" width="6" height="4" rx="2"/>
              <path d="M9 12h6m-6 4h6"/>
            </svg>
            Drafty k potvrzení (<span id="drafts-count">0</span>)
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(drawer);
  }

  injectStyles() {
    if (document.getElementById('ai-operator-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'ai-operator-styles';
    styles.textContent = `
      /* AI Operator Button in Header */
      .ai-operator-btn {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
        margin-right: 8px;
      }

      .ai-operator-btn:hover {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.25) 100%);
        border-color: rgba(99, 102, 241, 0.5);
        transform: scale(1.05);
      }

      .ai-operator-btn svg {
        width: 22px;
        height: 22px;
        stroke: #a78bfa;
        transition: stroke 0.2s;
      }

      .ai-operator-btn:hover svg {
        stroke: #c4b5fd;
      }

      .ai-operator-btn.has-critical {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
        border-color: rgba(239, 68, 68, 0.4);
        animation: pulse-critical 2s infinite;
      }

      .ai-operator-btn.has-critical svg {
        stroke: #f87171;
      }

      @keyframes pulse-critical {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); }
      }

      .ai-operator-badge {
        position: absolute;
        top: -4px;
        right: -4px;
        min-width: 18px;
        height: 18px;
        padding: 0 5px;
        background: #ef4444;
        color: white;
        font-size: 11px;
        font-weight: 600;
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .ai-operator-offline {
        position: absolute;
        bottom: -2px;
        right: -2px;
        font-size: 10px;
        background: #1e293b;
        border-radius: 4px;
        padding: 1px 3px;
      }

      /* Drawer Overlay & Panel */
      .ai-drawer {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: 9999;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
      }

      .ai-drawer.open {
        pointer-events: auto;
        opacity: 1;
      }

      .ai-drawer-overlay {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(2px);
      }

      .ai-drawer-panel {
        position: absolute;
        top: 0;
        right: -420px;
        width: 420px;
        max-width: 100vw;
        height: 100%;
        background: linear-gradient(180deg, #1a1f2e 0%, #151a27 100%);
        border-left: 1px solid #2d3748;
        display: flex;
        flex-direction: column;
        transition: right 0.3s ease;
        box-shadow: -10px 0 40px rgba(0, 0, 0, 0.3);
      }

      .ai-drawer.open .ai-drawer-panel {
        right: 0;
      }

      /* Drawer Header */
      .ai-drawer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 20px;
        border-bottom: 1px solid #2d3748;
        background: rgba(99, 102, 241, 0.05);
      }

      .ai-drawer-title {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .ai-drawer-title svg {
        width: 32px;
        height: 32px;
        stroke: #a78bfa;
      }

      .ai-drawer-title h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #f1f5f9;
      }

      .ai-drawer-subtitle {
        font-size: 12px;
        color: #64748b;
      }

      .ai-drawer-header-actions {
        display: flex;
        gap: 8px;
      }

      .ai-drawer-header-actions button {
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid #374151;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
      }

      .ai-drawer-header-actions button:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: #4b5563;
      }

      .ai-drawer-header-actions button svg {
        width: 18px;
        height: 18px;
        stroke: #9ca3af;
      }

      /* Tabs */
      .ai-drawer-tabs {
        display: flex;
        padding: 12px 16px;
        gap: 8px;
        border-bottom: 1px solid #2d3748;
      }

      .ai-tab {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 10px 12px;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 8px;
        color: #9ca3af;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }

      .ai-tab:hover {
        background: rgba(255, 255, 255, 0.05);
      }

      .ai-tab.active {
        background: rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.3);
        color: #c4b5fd;
      }

      .ai-tab-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
      }

      .ai-tab-dot.critical { background: #ef4444; }
      .ai-tab-dot.warning { background: #f59e0b; }
      .ai-tab-dot.info { background: #8b5cf6; }

      .ai-tab-count {
        background: rgba(255, 255, 255, 0.1);
        padding: 2px 6px;
        border-radius: 10px;
        font-size: 11px;
      }

      /* Filters */
      .ai-drawer-filters {
        display: flex;
        padding: 12px 16px;
        gap: 6px;
        flex-wrap: wrap;
        border-bottom: 1px solid #2d3748;
      }

      .ai-filter {
        padding: 6px 12px;
        background: transparent;
        border: 1px solid #374151;
        border-radius: 16px;
        color: #9ca3af;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s;
      }

      .ai-filter:hover {
        border-color: #4b5563;
        color: #e5e7eb;
      }

      .ai-filter.active {
        background: rgba(99, 102, 241, 0.2);
        border-color: rgba(99, 102, 241, 0.4);
        color: #c4b5fd;
      }

      /* Content */
      .ai-drawer-content {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
      }

      .ai-loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: #64748b;
        gap: 12px;
      }

      .ai-loading-spinner {
        width: 32px;
        height: 32px;
        border: 3px solid #374151;
        border-top-color: #8b5cf6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        to { transform: rotate(360deg); }
      }

      /* Insight Cards */
      .ai-insight-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        transition: all 0.2s;
      }

      .ai-insight-card:hover {
        border-color: #4b5563;
        background: rgba(255, 255, 255, 0.05);
      }

      .ai-insight-card.critical {
        border-left: 3px solid #ef4444;
      }

      .ai-insight-card.warning {
        border-left: 3px solid #f59e0b;
      }

      .ai-insight-card.info {
        border-left: 3px solid #8b5cf6;
      }

      .ai-insight-header {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        margin-bottom: 8px;
      }

      .ai-insight-title {
        font-size: 14px;
        font-weight: 600;
        color: #f1f5f9;
        margin: 0;
      }

      .ai-insight-severity {
        font-size: 10px;
        padding: 3px 8px;
        border-radius: 10px;
        font-weight: 500;
        text-transform: uppercase;
      }

      .ai-insight-severity.critical {
        background: rgba(239, 68, 68, 0.2);
        color: #fca5a5;
      }

      .ai-insight-severity.warning {
        background: rgba(245, 158, 11, 0.2);
        color: #fcd34d;
      }

      .ai-insight-severity.info {
        background: rgba(139, 92, 246, 0.2);
        color: #c4b5fd;
      }

      .ai-insight-impact {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 11px;
        color: #f59e0b;
        margin-bottom: 8px;
      }

      .ai-insight-evidence {
        font-size: 13px;
        color: #94a3b8;
        margin-bottom: 12px;
        line-height: 1.5;
      }

      .ai-insight-evidence a {
        color: #8b5cf6;
        text-decoration: none;
      }

      .ai-insight-evidence a:hover {
        text-decoration: underline;
      }

      .ai-insight-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 11px;
        color: #64748b;
        margin-bottom: 12px;
      }

      .ai-insight-confidence {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .ai-insight-confidence.high { color: #4ade80; }
      .ai-insight-confidence.medium { color: #fbbf24; }
      .ai-insight-confidence.low { color: #94a3b8; }

      .ai-insight-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }

      .ai-btn {
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 500;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.2s;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .ai-btn-primary {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border: none;
        color: white;
      }

      .ai-btn-primary:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
      }

      .ai-btn-secondary {
        background: transparent;
        border: 1px solid #374151;
        color: #9ca3af;
      }

      .ai-btn-secondary:hover {
        border-color: #4b5563;
        color: #e5e7eb;
      }

      .ai-btn-ghost {
        background: transparent;
        border: none;
        color: #64748b;
        padding: 6px 10px;
      }

      .ai-btn-ghost:hover {
        color: #9ca3af;
      }

      /* Drafts Panel */
      .ai-drawer-drafts {
        border-top: 1px solid #2d3748;
        padding: 12px 16px;
        background: rgba(0, 0, 0, 0.2);
      }

      .ai-drafts-toggle {
        width: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        padding: 12px;
        background: rgba(99, 102, 241, 0.1);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 8px;
        color: #a78bfa;
        font-size: 13px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
      }

      .ai-drafts-toggle:hover {
        background: rgba(99, 102, 241, 0.2);
        border-color: rgba(99, 102, 241, 0.4);
      }

      .ai-drafts-toggle svg {
        width: 18px;
        height: 18px;
        stroke: currentColor;
      }

      /* Empty State */
      .ai-empty {
        text-align: center;
        padding: 40px 20px;
        color: #64748b;
      }

      .ai-empty svg {
        width: 48px;
        height: 48px;
        stroke: #4b5563;
        margin-bottom: 12px;
      }

      .ai-empty h3 {
        margin: 0 0 8px;
        font-size: 16px;
        color: #94a3b8;
      }

      .ai-empty p {
        margin: 0;
        font-size: 13px;
      }

      /* Mobile */
      @media (max-width: 480px) {
        .ai-drawer-panel {
          width: 100%;
          right: -100%;
        }

        .ai-operator-btn {
          width: 36px;
          height: 36px;
        }

        .ai-operator-btn svg {
          width: 18px;
          height: 18px;
        }
      }
    `;

    document.head.appendChild(styles);
  }

  bindEvents() {
    // Toggle button
    document.addEventListener('click', (e) => {
      const toggle = e.target.closest('#ai-operator-toggle');
      if (toggle) {
        this.toggle();
        return;
      }

      const close = e.target.closest('#ai-drawer-close');
      const overlay = e.target.closest('#ai-drawer-overlay');
      if (close || overlay) {
        this.close();
        return;
      }

      // Tab switching
      const tab = e.target.closest('.ai-tab');
      if (tab) {
        this.switchTab(tab.dataset.tab);
        return;
      }

      // Filter switching
      const filter = e.target.closest('.ai-filter');
      if (filter) {
        this.switchFilter(filter.dataset.filter);
        return;
      }

      // Create draft
      const createDraft = e.target.closest('.ai-create-draft');
      if (createDraft) {
        this.createDraft(createDraft.dataset);
        return;
      }

      // Snooze
      const snooze = e.target.closest('.ai-snooze');
      if (snooze) {
        this.snoozeInsight(snooze.dataset.id);
        return;
      }

      // Dismiss
      const dismiss = e.target.closest('.ai-dismiss');
      if (dismiss) {
        this.dismissInsight(dismiss.dataset.id);
        return;
      }

      // Open detail link
      const detailLink = e.target.closest('.ai-detail-link');
      if (detailLink) {
        this.close();
        return;
      }

      // Digest
      const digest = e.target.closest('#ai-digest-btn');
      if (digest) {
        this.showDigest();
        return;
      }

      // Drafts toggle
      const draftsToggle = e.target.closest('#ai-drafts-toggle');
      if (draftsToggle) {
        this.showDrafts();
        return;
      }
    });

    // Keyboard
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
    const drawer = document.getElementById('ai-operator-drawer');
    if (drawer) {
      drawer.classList.add('open');
      this.isOpen = true;
      document.body.style.overflow = 'hidden';
      this.loadInsights();
    }
  }

  close() {
    const drawer = document.getElementById('ai-operator-drawer');
    if (drawer) {
      drawer.classList.remove('open');
      this.isOpen = false;
      document.body.style.overflow = '';
    }
  }

  switchTab(tab) {
    this.activeTab = tab;
    document.querySelectorAll('.ai-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tab);
    });
    this.renderInsights();
  }

  switchFilter(filter) {
    this.activeFilter = filter;
    document.querySelectorAll('.ai-filter').forEach(f => {
      f.classList.toggle('active', f.dataset.filter === filter);
    });
    this.renderInsights();
  }

  async loadInsights() {
    try {
      const response = await fetch('/api/ai/dashboard');
      const data = await response.json();
      
      // Transform data to unified format
      this.insights = this.transformInsights(data);
      this.updateBadge();
      this.updateCounts();
      this.renderInsights();
    } catch (err) {
      console.error('Failed to load AI insights:', err);
      this.renderError();
    }
  }

  transformInsights(data) {
    const insights = [];

    // Transform warnings
    if (data.warnings) {
      data.warnings.forEach((w, i) => {
        insights.push({
          id: `warn_${i}`,
          type: this.mapSeverity(w.severity),
          category: this.detectCategory(w),
          title: w.title || w.message || 'Varování',
          evidence: w.details || w.evidence || '',
          impact: w.impact || '',
          confidence: w.confidence || 'medium',
          link: w.link || w.url || null,
          linkText: w.linkText || 'Zobrazit',
          actions: w.actions || this.getDefaultActions(w)
        });
      });
    }

    // Transform recommendations
    if (data.recommendations) {
      data.recommendations.forEach((r, i) => {
        insights.push({
          id: `rec_${i}`,
          type: 'info',
          category: this.detectCategory(r),
          title: r.title || r.message || 'Doporučení',
          evidence: r.details || r.evidence || '',
          impact: r.impact || '',
          confidence: r.confidence || 'medium',
          link: r.link || r.url || null,
          linkText: r.linkText || 'Zobrazit',
          actions: r.actions || this.getDefaultActions(r)
        });
      });
    }

    return insights;
  }

  mapSeverity(severity) {
    const map = {
      'critical': 'critical',
      'high': 'critical',
      'medium': 'warning',
      'low': 'info'
    };
    return map[severity] || 'info';
  }

  detectCategory(item) {
    const text = JSON.stringify(item).toLowerCase();
    if (text.includes('zakázk') || text.includes('job')) return 'jobs';
    if (text.includes('úkol') || text.includes('task')) return 'tasks';
    if (text.includes('zaměstnan') || text.includes('employ') || text.includes('tým')) return 'team';
    if (text.includes('sklad') || text.includes('materiál') || text.includes('stock')) return 'warehouse';
    if (text.includes('výkaz') || text.includes('timesheet') || text.includes('hodin')) return 'timesheets';
    return 'other';
  }

  getDefaultActions(item) {
    return [
      { type: 'draft', label: 'Vytvořit draft', action: item.draft_action || 'GENERIC' },
      { type: 'link', label: 'Zobrazit detail' }
    ];
  }

  updateBadge() {
    const badge = document.getElementById('ai-operator-badge');
    const btn = document.getElementById('ai-operator-toggle');
    
    const criticalCount = this.insights.filter(i => i.type === 'critical').length;
    const warningCount = this.insights.filter(i => i.type === 'warning').length;
    const total = criticalCount + warningCount;

    if (badge) {
      badge.textContent = total;
      badge.style.display = total > 0 ? 'flex' : 'none';
    }

    if (btn) {
      btn.classList.toggle('has-critical', criticalCount > 0);
    }
  }

  updateCounts() {
    const counts = {
      critical: this.insights.filter(i => i.type === 'critical').length,
      warning: this.insights.filter(i => i.type === 'warning').length,
      info: this.insights.filter(i => i.type === 'info').length
    };

    Object.entries(counts).forEach(([type, count]) => {
      const el = document.getElementById(`${type}-count`);
      if (el) el.textContent = count;
    });
  }

  renderInsights() {
    const container = document.getElementById('ai-drawer-content');
    if (!container) return;

    // Filter insights
    let filtered = this.insights.filter(i => i.type === this.activeTab);
    
    if (this.activeFilter !== 'all') {
      filtered = filtered.filter(i => i.category === this.activeFilter);
    }

    if (filtered.length === 0) {
      container.innerHTML = this.renderEmpty();
      return;
    }

    container.innerHTML = filtered.map(insight => this.renderInsightCard(insight)).join('');
  }

  renderInsightCard(insight) {
    const severityLabels = {
      critical: 'Kritické',
      warning: 'Varování',
      info: 'Doporučení'
    };

    return `
      <div class="ai-insight-card ${insight.type}">
        <div class="ai-insight-header">
          <h4 class="ai-insight-title">${this.escapeHtml(insight.title)}</h4>
          <span class="ai-insight-severity ${insight.type}">${severityLabels[insight.type]}</span>
        </div>
        
        ${insight.impact ? `
          <div class="ai-insight-impact">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            ${this.escapeHtml(insight.impact)}
          </div>
        ` : ''}
        
        <div class="ai-insight-evidence">
          ${this.escapeHtml(insight.evidence)}
          ${insight.link ? `<a href="${insight.link}" class="ai-detail-link">${insight.linkText}</a>` : ''}
        </div>
        
        <div class="ai-insight-meta">
          <span class="ai-insight-confidence ${insight.confidence}">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12l2 2 4-4"/>
              <circle cx="12" cy="12" r="10"/>
            </svg>
            ${insight.confidence === 'high' ? 'Vysoká' : insight.confidence === 'medium' ? 'Střední' : 'Nízká'} jistota
          </span>
        </div>
        
        <div class="ai-insight-actions">
          <button class="ai-btn ai-btn-primary ai-create-draft" data-id="${insight.id}" data-action="${insight.actions?.[0]?.action || 'GENERIC'}">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
              <rect x="9" y="3" width="6" height="4" rx="2"/>
            </svg>
            Vytvořit draft
          </button>
          ${insight.link ? `
            <a href="${insight.link}" class="ai-btn ai-btn-secondary ai-detail-link">Otevřít detail</a>
          ` : ''}
          <button class="ai-btn ai-btn-ghost ai-snooze" data-id="${insight.id}" title="Odložit na později">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </button>
          <button class="ai-btn ai-btn-ghost ai-dismiss" data-id="${insight.id}" title="Zamítnout">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>
      </div>
    `;
  }

  renderEmpty() {
    return `
      <div class="ai-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
          <line x1="9" y1="9" x2="9.01" y2="9"/>
          <line x1="15" y1="9" x2="15.01" y2="9"/>
        </svg>
        <h3>Vše v pořádku</h3>
        <p>Žádné ${this.activeTab === 'critical' ? 'kritické problémy' : this.activeTab === 'warning' ? 'varování' : 'doporučení'} k řešení.</p>
      </div>
    `;
  }

  renderError() {
    const container = document.getElementById('ai-drawer-content');
    if (!container) return;

    container.innerHTML = `
      <div class="ai-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M12 8v4m0 4h.01"/>
        </svg>
        <h3>Chyba načítání</h3>
        <p>Nepodařilo se načíst data. Zkuste to později.</p>
      </div>
    `;
  }

  async createDraft(data) {
    try {
      const response = await fetch('/api/ai/drafts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          insight_id: data.id,
          action_type: data.action
        })
      });

      if (response.ok) {
        this.showToast('Draft vytvořen', 'success');
        this.loadInsights();
      } else {
        this.showToast('Chyba při vytváření draftu', 'error');
      }
    } catch (err) {
      console.error('Create draft error:', err);
      this.showToast('Chyba při vytváření draftu', 'error');
    }
  }

  async snoozeInsight(id) {
    try {
      await fetch(`/api/ai/insights/${id}/snooze`, { method: 'POST' });
      this.insights = this.insights.filter(i => i.id !== id);
      this.updateBadge();
      this.updateCounts();
      this.renderInsights();
      this.showToast('Odloženo na později', 'info');
    } catch (err) {
      console.error('Snooze error:', err);
    }
  }

  async dismissInsight(id) {
    try {
      await fetch(`/api/ai/insights/${id}/dismiss`, { method: 'POST' });
      this.insights = this.insights.filter(i => i.id !== id);
      this.updateBadge();
      this.updateCounts();
      this.renderInsights();
      this.showToast('Zamítnuto', 'info');
    } catch (err) {
      console.error('Dismiss error:', err);
    }
  }

  showDigest() {
    // TODO: Implement digest modal
    this.showToast('Digest bude brzy k dispozici', 'info');
  }

  showDrafts() {
    // Navigate to drafts page or open modal
    window.location.href = '/ai-operator.html#drafts';
    this.close();
  }

  showToast(message, type = 'info') {
    // Use existing toast if available
    if (typeof window.showToast === 'function') {
      window.showToast(message, type);
      return;
    }

    // Simple fallback toast
    const toast = document.createElement('div');
    toast.style.cssText = `
      position: fixed;
      bottom: 80px;
      left: 50%;
      transform: translateX(-50%);
      padding: 12px 20px;
      background: ${type === 'success' ? '#059669' : type === 'error' ? '#dc2626' : '#6366f1'};
      color: white;
      border-radius: 8px;
      font-size: 14px;
      z-index: 10000;
      animation: fadeInUp 0.3s ease;
    `;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  startPolling() {
    // Poll every 60 seconds
    setInterval(() => {
      if (!this.isOpen) {
        this.loadInsights();
      }
    }, 60000);
  }

  monitorConnection() {
    window.addEventListener('online', () => {
      this.isOffline = false;
      document.getElementById('ai-operator-offline')?.style.setProperty('display', 'none');
      this.loadInsights();
    });

    window.addEventListener('offline', () => {
      this.isOffline = true;
      document.getElementById('ai-operator-offline')?.style.setProperty('display', 'block');
    });
  }

  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize when DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.aiOperator = new AIOperatorDrawer();
  });
} else {
  window.aiOperator = new AIOperatorDrawer();
}
