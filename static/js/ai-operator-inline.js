/**
 * AI OPERATOR INLINE INDICATORS
 * ==============================
 * Inline indikátory AI Operátora ve všech sekcích aplikace
 * Badge a značky přímo v UI komponentách
 */

class AIInlineIndicators {
  constructor() {
    this.insights = {};
    this.init();
  }

  async init() {
    await this.loadInsights();
    this.injectIndicators();
    this.observeDOM();
  }

  async loadInsights() {
    try {
      const response = await fetch('/api/ai/dashboard');
      const data = await response.json();
      this.processInsights(data);
    } catch (err) {
      console.error('Failed to load AI insights for indicators:', err);
    }
  }

  processInsights(data) {
    // Index insights by entity
    this.insights = {
      jobs: {},
      tasks: {},
      employees: {},
      warehouse: {},
      timesheets: {}
    };

    // Process warnings
    (data.warnings || []).forEach(w => {
      this.indexInsight(w, this.mapSeverity(w.severity));
    });

    // Process recommendations
    (data.recommendations || []).forEach(r => {
      this.indexInsight(r, 'info');
    });
  }

  indexInsight(item, severity) {
    // Try to extract job_id
    if (item.job_id) {
      if (!this.insights.jobs[item.job_id]) {
        this.insights.jobs[item.job_id] = [];
      }
      this.insights.jobs[item.job_id].push({ ...item, severity });
    }

    // Try to extract employee_id
    if (item.employee_id) {
      if (!this.insights.employees[item.employee_id]) {
        this.insights.employees[item.employee_id] = [];
      }
      this.insights.employees[item.employee_id].push({ ...item, severity });
    }

    // Try to extract task_id
    if (item.task_id) {
      if (!this.insights.tasks[item.task_id]) {
        this.insights.tasks[item.task_id] = [];
      }
      this.insights.tasks[item.task_id].push({ ...item, severity });
    }

    // Try to extract warehouse item
    if (item.item_id || item.warehouse_id) {
      const id = item.item_id || item.warehouse_id;
      if (!this.insights.warehouse[id]) {
        this.insights.warehouse[id] = [];
      }
      this.insights.warehouse[id].push({ ...item, severity });
    }
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

  injectIndicators() {
    this.injectStyles();
    this.injectJobIndicators();
    this.injectTaskIndicators();
    this.injectEmployeeIndicators();
    this.injectWarehouseIndicators();
  }

  injectStyles() {
    if (document.getElementById('ai-inline-styles')) return;

    const styles = document.createElement('style');
    styles.id = 'ai-inline-styles';
    styles.textContent = `
      /* AI Inline Indicator Badges */
      .ai-indicator {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 6px;
        font-size: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
        position: relative;
      }

      .ai-indicator:hover {
        transform: scale(1.15);
      }

      .ai-indicator svg {
        width: 14px;
        height: 14px;
      }

      .ai-indicator.critical {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
      }

      .ai-indicator.warning {
        background: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
      }

      .ai-indicator.info {
        background: rgba(139, 92, 246, 0.2);
        color: #a78bfa;
      }

      /* AI Badge Group */
      .ai-badge-group {
        display: inline-flex;
        gap: 4px;
        margin-left: 8px;
      }

      /* AI Tooltip */
      .ai-indicator-tooltip {
        position: absolute;
        bottom: calc(100% + 8px);
        left: 50%;
        transform: translateX(-50%);
        padding: 8px 12px;
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #e2e8f0;
        font-size: 12px;
        white-space: nowrap;
        max-width: 250px;
        white-space: normal;
        z-index: 1000;
        opacity: 0;
        visibility: hidden;
        transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      }

      .ai-indicator-tooltip::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        border: 6px solid transparent;
        border-top-color: #334155;
      }

      .ai-indicator:hover .ai-indicator-tooltip {
        opacity: 1;
        visibility: visible;
      }

      /* Capacity Ring for Employees */
      .ai-capacity-ring {
        position: relative;
        width: 36px;
        height: 36px;
      }

      .ai-capacity-ring svg {
        width: 100%;
        height: 100%;
        transform: rotate(-90deg);
      }

      .ai-capacity-ring circle {
        fill: none;
        stroke-width: 3;
      }

      .ai-capacity-ring .bg {
        stroke: #374151;
      }

      .ai-capacity-ring .progress {
        stroke-linecap: round;
        transition: stroke-dashoffset 0.5s ease;
      }

      .ai-capacity-ring .progress.normal { stroke: #4ade80; }
      .ai-capacity-ring .progress.warning { stroke: #fbbf24; }
      .ai-capacity-ring .progress.critical { stroke: #ef4444; }

      .ai-capacity-value {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-size: 10px;
        font-weight: 600;
        color: #e2e8f0;
      }

      /* Ghost Overlay for Timeline */
      .ai-ghost-block {
        position: absolute;
        background: repeating-linear-gradient(
          45deg,
          rgba(139, 92, 246, 0.1),
          rgba(139, 92, 246, 0.1) 10px,
          rgba(139, 92, 246, 0.2) 10px,
          rgba(139, 92, 246, 0.2) 20px
        );
        border: 2px dashed rgba(139, 92, 246, 0.5);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
      }

      .ai-ghost-block:hover {
        background: rgba(139, 92, 246, 0.25);
        border-color: rgba(139, 92, 246, 0.7);
      }

      .ai-ghost-block .ai-ghost-label {
        padding: 4px 8px;
        background: rgba(139, 92, 246, 0.3);
        border-radius: 4px;
        font-size: 11px;
        color: #c4b5fd;
      }

      /* Warehouse Stock Level Bar */
      .ai-stock-level {
        height: 4px;
        background: #374151;
        border-radius: 2px;
        overflow: hidden;
        margin-top: 4px;
      }

      .ai-stock-level-fill {
        height: 100%;
        border-radius: 2px;
        transition: width 0.3s ease;
      }

      .ai-stock-level-fill.good { background: #4ade80; }
      .ai-stock-level-fill.warning { background: #fbbf24; }
      .ai-stock-level-fill.critical { background: #ef4444; }

      /* Inline Warning Banner */
      .ai-inline-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 8px;
        margin-bottom: 16px;
      }

      .ai-inline-banner.critical {
        background: rgba(239, 68, 68, 0.1);
        border-color: rgba(239, 68, 68, 0.3);
      }

      .ai-inline-banner.warning {
        background: rgba(245, 158, 11, 0.1);
        border-color: rgba(245, 158, 11, 0.3);
      }

      .ai-inline-banner svg {
        width: 20px;
        height: 20px;
        flex-shrink: 0;
      }

      .ai-inline-banner.critical svg { stroke: #f87171; }
      .ai-inline-banner.warning svg { stroke: #fbbf24; }
      .ai-inline-banner.info svg { stroke: #a78bfa; }

      .ai-inline-banner-text {
        flex: 1;
        font-size: 13px;
        color: #e2e8f0;
      }

      .ai-inline-banner-action {
        padding: 6px 12px;
        background: rgba(255, 255, 255, 0.1);
        border: none;
        border-radius: 6px;
        color: #e2e8f0;
        font-size: 12px;
        cursor: pointer;
        transition: background 0.2s;
      }

      .ai-inline-banner-action:hover {
        background: rgba(255, 255, 255, 0.2);
      }
    `;

    document.head.appendChild(styles);
  }

  injectJobIndicators() {
    // Find job cards
    const jobCards = document.querySelectorAll('[data-job-id], .job-card, .kanban-card');
    
    jobCards.forEach(card => {
      const jobId = card.dataset.jobId || card.getAttribute('data-id');
      if (!jobId) return;

      const insights = this.insights.jobs[jobId];
      if (!insights || insights.length === 0) return;

      // Remove existing indicators
      card.querySelector('.ai-badge-group')?.remove();

      // Create badge group
      const badges = this.createBadgeGroup(insights);
      
      // Find title element or header
      const header = card.querySelector('.job-title, .card-title, .kanban-card-title, h3, h4');
      if (header) {
        header.style.display = 'flex';
        header.style.alignItems = 'center';
        header.appendChild(badges);
      }
    });
  }

  injectTaskIndicators() {
    // Find task items
    const taskItems = document.querySelectorAll('[data-task-id], .task-item, .task-card');
    
    taskItems.forEach(item => {
      const taskId = item.dataset.taskId || item.getAttribute('data-id');
      if (!taskId) return;

      const insights = this.insights.tasks[taskId];
      if (!insights || insights.length === 0) return;

      item.querySelector('.ai-badge-group')?.remove();

      const badges = this.createBadgeGroup(insights);
      const header = item.querySelector('.task-title, .task-name, h4');
      if (header) {
        header.style.display = 'flex';
        header.style.alignItems = 'center';
        header.appendChild(badges);
      }
    });
  }

  injectEmployeeIndicators() {
    // Find employee cards/rows
    const employeeItems = document.querySelectorAll('[data-employee-id], .employee-card, .employee-row');
    
    employeeItems.forEach(item => {
      const employeeId = item.dataset.employeeId || item.getAttribute('data-id');
      if (!employeeId) return;

      const insights = this.insights.employees[employeeId];
      
      // Add capacity ring if we have workload data
      const capacityContainer = item.querySelector('.employee-capacity, .capacity-container');
      if (capacityContainer) {
        this.injectCapacityRing(capacityContainer, insights);
      }

      // Add badges
      if (insights && insights.length > 0) {
        item.querySelector('.ai-badge-group')?.remove();
        const badges = this.createBadgeGroup(insights);
        const header = item.querySelector('.employee-name, h4, .name');
        if (header) {
          header.style.display = 'flex';
          header.style.alignItems = 'center';
          header.appendChild(badges);
        }
      }
    });
  }

  injectWarehouseIndicators() {
    // Find warehouse items
    const warehouseItems = document.querySelectorAll('[data-item-id], .warehouse-item, .stock-item');
    
    warehouseItems.forEach(item => {
      const itemId = item.dataset.itemId || item.getAttribute('data-id');
      if (!itemId) return;

      const insights = this.insights.warehouse[itemId];
      
      // Add stock level bar
      const qtyContainer = item.querySelector('.item-qty, .stock-qty, .quantity');
      if (qtyContainer) {
        this.injectStockLevel(qtyContainer, insights);
      }

      // Add badges
      if (insights && insights.length > 0) {
        item.querySelector('.ai-badge-group')?.remove();
        const badges = this.createBadgeGroup(insights);
        const header = item.querySelector('.item-name, h4, .name');
        if (header) {
          header.style.display = 'flex';
          header.style.alignItems = 'center';
          header.appendChild(badges);
        }
      }
    });
  }

  createBadgeGroup(insights) {
    const group = document.createElement('div');
    group.className = 'ai-badge-group';

    // Group by type
    const types = {
      critical: insights.filter(i => i.severity === 'critical'),
      warning: insights.filter(i => i.severity === 'warning'),
      info: insights.filter(i => i.severity === 'info')
    };

    // Show max 3 badges
    let count = 0;
    for (const [type, items] of Object.entries(types)) {
      if (items.length > 0 && count < 3) {
        const badge = this.createBadge(type, items);
        group.appendChild(badge);
        count++;
      }
    }

    return group;
  }

  createBadge(type, insights) {
    const badge = document.createElement('div');
    badge.className = `ai-indicator ${type}`;
    badge.innerHTML = `
      ${this.getTypeIcon(type)}
      <div class="ai-indicator-tooltip">
        <strong>${insights.length}x ${this.getTypeLabel(type)}</strong><br>
        ${insights[0].title || insights[0].message || 'Klikněte pro detail'}
      </div>
    `;

    badge.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      window.aiOperator?.open();
    });

    return badge;
  }

  getTypeIcon(type) {
    const icons = {
      critical: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>`,
      warning: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
      </svg>`,
      info: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4m0-4h.01"/>
      </svg>`
    };
    return icons[type] || icons.info;
  }

  getTypeLabel(type) {
    const labels = {
      critical: 'Kritické',
      warning: 'Varování',
      info: 'Doporučení'
    };
    return labels[type] || 'Info';
  }

  injectCapacityRing(container, insights) {
    // Get capacity from insights or default
    let capacity = 50; // default
    let status = 'normal';

    if (insights) {
      const overload = insights.find(i => i.title?.includes('přetížen') || i.message?.includes('přetížen'));
      if (overload) {
        capacity = 95;
        status = 'critical';
      }
    }

    const circumference = 2 * Math.PI * 14;
    const offset = circumference - (capacity / 100) * circumference;

    container.innerHTML = `
      <div class="ai-capacity-ring">
        <svg viewBox="0 0 36 36">
          <circle class="bg" cx="18" cy="18" r="14"/>
          <circle class="progress ${status}" cx="18" cy="18" r="14" 
            stroke-dasharray="${circumference}" 
            stroke-dashoffset="${offset}"/>
        </svg>
        <span class="ai-capacity-value">${capacity}%</span>
      </div>
    `;
  }

  injectStockLevel(container, insights) {
    // Determine stock level status
    let level = 80;
    let status = 'good';

    if (insights) {
      const lowStock = insights.find(i => i.title?.includes('nízký') || i.message?.includes('minimum'));
      if (lowStock) {
        level = 15;
        status = 'critical';
      }
    }

    const levelBar = document.createElement('div');
    levelBar.className = 'ai-stock-level';
    levelBar.innerHTML = `<div class="ai-stock-level-fill ${status}" style="width: ${level}%"></div>`;
    
    // Don't duplicate
    if (!container.querySelector('.ai-stock-level')) {
      container.appendChild(levelBar);
    }
  }

  observeDOM() {
    // Re-inject indicators when DOM changes (e.g., after AJAX loads)
    const observer = new MutationObserver((mutations) => {
      let shouldUpdate = false;
      mutations.forEach(m => {
        if (m.addedNodes.length > 0) {
          m.addedNodes.forEach(node => {
            if (node.nodeType === 1 && (
              node.matches?.('[data-job-id], [data-task-id], [data-employee-id], [data-item-id]') ||
              node.querySelector?.('[data-job-id], [data-task-id], [data-employee-id], [data-item-id]')
            )) {
              shouldUpdate = true;
            }
          });
        }
      });
      
      if (shouldUpdate) {
        setTimeout(() => this.injectIndicators(), 100);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  // Public method to create inline banner
  static createBanner(type, message, actionText, actionCallback) {
    const banner = document.createElement('div');
    banner.className = `ai-inline-banner ${type}`;
    banner.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <circle cx="12" cy="12" r="6"/>
        <circle cx="12" cy="12" r="2"/>
        <line x1="12" y1="2" x2="12" y2="6"/>
        <line x1="12" y1="18" x2="12" y2="22"/>
        <line x1="2" y1="12" x2="6" y2="12"/>
        <line x1="18" y1="12" x2="22" y2="12"/>
      </svg>
      <span class="ai-inline-banner-text">${message}</span>
      ${actionText ? `<button class="ai-inline-banner-action">${actionText}</button>` : ''}
    `;

    if (actionCallback) {
      banner.querySelector('.ai-inline-banner-action')?.addEventListener('click', actionCallback);
    }

    return banner;
  }
}

// Initialize when DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.aiIndicators = new AIInlineIndicators();
  });
} else {
  window.aiIndicators = new AIInlineIndicators();
}
