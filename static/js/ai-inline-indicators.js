/**
 * AI OPERATOR INLINE INDICATORS
 * ==============================
 * Přidává vizuální indikátory (badge) na karty zakázek, úkolů, členů teamu.
 * 
 * Typy indikátorů:
 * - ⚠️ deadline (termín)
 * - 💰 budget (rozpočet)
 * - 📦 material (materiál)
 * - 🌧️ weather (počasí)
 * - 👷 workload (přetížení)
 */

class AIInlineIndicators {
    constructor() {
        this.indicators = {};
        this.init();
    }

    // SVG ikony jako mini badge
    get icons() {
        return {
            deadline: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
            budget: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>`,
            material: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M16.5 9.4l-9-5.19"/><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>`,
            weather: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z"/></svg>`,
            workload: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>`,
            brain: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 2a7 7 0 00-7 7c0 2.38 1.19 4.47 3 5.74V17a2 2 0 002 2h4a2 2 0 002-2v-2.26c1.81-1.27 3-3.36 3-5.74a7 7 0 00-7-7Z"/></svg>`
        };
    }

    init() {
        this.injectStyles();
        
        // Auto-detect current page and apply indicators
        const path = window.location.pathname;
        
        if (path.includes('jobs.html') || path.includes('jobs-new.html')) {
            this.initJobsPage();
        } else if (path.includes('tasks.html')) {
            this.initTasksPage();
        } else if (path.includes('employees.html') || path.includes('team.html')) {
            this.initTeamPage();
        } else if (path.includes('timeline.html') || path.includes('planning-timeline.html')) {
            this.initTimelinePage();
        } else if (path.includes('warehouse.html')) {
            this.initWarehousePage();
        }
    }

    injectStyles() {
        if (document.getElementById('ai-inline-indicators-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'ai-inline-indicators-styles';
        style.textContent = `
            /* AI Inline Indicator Badge */
            .ai-indicator-badge {
                display: inline-flex;
                align-items: center;
                gap: 3px;
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
                text-transform: uppercase;
                letter-spacing: 0.3px;
            }
            .ai-indicator-badge svg {
                flex-shrink: 0;
            }
            .ai-indicator-badge:hover {
                transform: scale(1.05);
            }

            /* Severity colors */
            .ai-indicator-badge.critical {
                background: rgba(248, 113, 113, 0.2);
                color: #f87171;
                border: 1px solid rgba(248, 113, 113, 0.3);
            }
            .ai-indicator-badge.warn {
                background: rgba(251, 191, 36, 0.2);
                color: #fbbf24;
                border: 1px solid rgba(251, 191, 36, 0.3);
            }
            .ai-indicator-badge.info {
                background: rgba(96, 165, 250, 0.2);
                color: #60a5fa;
                border: 1px solid rgba(96, 165, 250, 0.3);
            }
            .ai-indicator-badge.success {
                background: rgba(74, 222, 128, 0.2);
                color: #4ade80;
                border: 1px solid rgba(74, 222, 128, 0.3);
            }

            /* Container for multiple badges */
            .ai-indicators-container {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
                margin-top: 6px;
            }

            /* Tooltip */
            .ai-indicator-badge[data-tooltip] {
                position: relative;
            }
            .ai-indicator-badge[data-tooltip]:hover::after {
                content: attr(data-tooltip);
                position: absolute;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                padding: 6px 10px;
                background: #1f2940;
                color: #fff;
                font-size: 11px;
                font-weight: normal;
                text-transform: none;
                letter-spacing: normal;
                white-space: nowrap;
                border-radius: 6px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                z-index: 100;
                margin-bottom: 4px;
            }

            /* Job card modifications for indicators */
            .job-card .ai-indicators-container,
            .kanban-card .ai-indicators-container {
                position: absolute;
                top: 8px;
                right: 8px;
            }
            .job-card, .kanban-card {
                position: relative;
            }

            /* Task card indicators */
            .task-card .ai-indicators-container {
                margin-left: auto;
            }

            /* Timeline block indicators */
            .timeline-block .ai-indicator-badge {
                position: absolute;
                top: 2px;
                right: 2px;
                padding: 2px 4px;
                font-size: 9px;
            }

            /* Mini mode for cramped spaces */
            .ai-indicator-badge.mini {
                padding: 2px 4px;
                font-size: 9px;
            }
            .ai-indicator-badge.mini svg {
                width: 10px;
                height: 10px;
            }
            .ai-indicator-badge.mini span {
                display: none;
            }

            /* Ghost overlay for AI recommendations */
            .ai-ghost-overlay {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(74, 222, 128, 0.1);
                border: 2px dashed rgba(74, 222, 128, 0.5);
                border-radius: inherit;
                pointer-events: none;
                z-index: 1;
            }
            .ai-ghost-overlay::before {
                content: '🧠 Doporučení AI';
                position: absolute;
                top: 4px;
                left: 4px;
                font-size: 10px;
                color: #4ade80;
                background: #1f2940;
                padding: 2px 6px;
                border-radius: 4px;
            }
        `;
        document.head.appendChild(style);
    }

    async initJobsPage() {
        // Wait for job cards to load
        await this.waitForElement('.job-card, .kanban-card, [data-job-id]');
        
        // Fetch all indicators at once
        try {
            const response = await fetch('/api/ai/all-job-indicators');
            const data = await response.json();
            this.indicators = data.indicators || {};
            this.applyJobIndicators();
        } catch (error) {
            debugLog('AI indicators not available');
        }
        
        // Observe for dynamically added cards
        this.observeJobCards();
    }

    applyJobIndicators() {
        // Find all job cards
        const jobCards = document.querySelectorAll('[data-job-id], .job-card[data-id], .kanban-card[data-id]');
        
        jobCards.forEach(card => {
            const jobId = card.dataset.jobId || card.dataset.id;
            if (!jobId) return;
            
            const indicators = this.indicators[jobId];
            if (!indicators || indicators.length === 0) return;
            
            // Check if already has indicators
            if (card.querySelector('.ai-indicators-container')) return;
            
            // Create container
            const container = document.createElement('div');
            container.className = 'ai-indicators-container';
            
            indicators.forEach(ind => {
                const badge = this.createBadge(ind.type, ind.severity, ind.value);
                container.appendChild(badge);
            });
            
            // Add to card
            card.style.position = 'relative';
            card.appendChild(container);
        });
    }

    createBadge(type, severity, value) {
        const badge = document.createElement('span');
        badge.className = `ai-indicator-badge ${severity || 'info'}`;
        
        const icon = this.icons[type] || this.icons.brain;
        const label = this.getTypeLabel(type);
        
        badge.innerHTML = `${icon}<span>${value || label}</span>`;
        badge.setAttribute('data-tooltip', this.getTooltip(type, severity, value));
        
        // Click opens AI Operator drawer filtered to this issue
        badge.addEventListener('click', (e) => {
            e.stopPropagation();
            if (window.aiOperatorDrawer) {
                window.aiOperatorDrawer.setFilter(this.mapTypeToFilter(type));
                window.aiOperatorDrawer.open();
            }
        });
        
        return badge;
    }

    getTypeLabel(type) {
        const labels = {
            deadline: 'Termín',
            budget: 'Rozpočet',
            material: 'Materiál',
            weather: 'Počasí',
            workload: 'Přetížení'
        };
        return labels[type] || type;
    }

    getTooltip(type, severity, value) {
        const tooltips = {
            deadline: {
                critical: 'Po termínu! Klikněte pro detaily.',
                warn: 'Termín se blíží. Klikněte pro detaily.'
            },
            budget: {
                critical: `Rozpočet překročen (${value}). Klikněte pro detaily.`,
                warn: `Blíží se limit rozpočtu (${value}). Klikněte pro detaily.`
            },
            material: {
                critical: 'Chybí materiál! Klikněte pro detaily.',
                warn: 'Materiál dochází. Klikněte pro detaily.'
            },
            weather: {
                critical: 'Nepříznivé počasí! Klikněte pro detaily.',
                warn: 'Možné riziko počasí. Klikněte pro detaily.',
                info: 'Venkovní zakázka. Klikněte pro info.'
            },
            workload: {
                critical: 'Přetížení týmu! Klikněte pro detaily.',
                warn: 'Vysoké vytížení. Klikněte pro detaily.'
            }
        };
        
        return tooltips[type]?.[severity] || 'Klikněte pro detaily';
    }

    mapTypeToFilter(type) {
        const mapping = {
            deadline: 'jobs',
            budget: 'jobs',
            material: 'warehouse',
            weather: 'weather',
            workload: 'team'
        };
        return mapping[type] || 'jobs';
    }

    observeJobCards() {
        const observer = new MutationObserver((mutations) => {
            let shouldUpdate = false;
            mutations.forEach(m => {
                if (m.addedNodes.length > 0) {
                    shouldUpdate = true;
                }
            });
            if (shouldUpdate) {
                setTimeout(() => this.applyJobIndicators(), 100);
            }
        });
        
        const container = document.querySelector('.jobs-grid, .kanban-board, .jobs-container, main');
        if (container) {
            observer.observe(container, { childList: true, subtree: true });
        }
    }

    async initTasksPage() {
        // Similar approach for tasks
        await this.waitForElement('.task-card, [data-task-id]');
        
        try {
            const response = await fetch('/api/ai/task-indicators');
            const data = await response.json();
            // Apply task indicators...
        } catch (error) {
            debugLog('Task indicators not available');
        }
    }

    async initTeamPage() {
        // Team/employees page indicators
        await this.waitForElement('.employee-card, [data-employee-id]');
        // ... implement similar to jobs
    }

    async initTimelinePage() {
        // Timeline blocks need ghost overlays for AI recommendations
        await this.waitForElement('.timeline-block, .planning-block');
        // ... implement ghost overlays
    }

    async initWarehousePage() {
        // Warehouse items with low stock indicators
        await this.waitForElement('.inventory-item, [data-item-id]');
        // ... implement
    }

    waitForElement(selector, timeout = 5000) {
        return new Promise((resolve) => {
            const element = document.querySelector(selector);
            if (element) {
                resolve(element);
                return;
            }
            
            const observer = new MutationObserver(() => {
                const el = document.querySelector(selector);
                if (el) {
                    observer.disconnect();
                    resolve(el);
                }
            });
            
            observer.observe(document.body, { childList: true, subtree: true });
            
            setTimeout(() => {
                observer.disconnect();
                resolve(null);
            }, timeout);
        });
    }

    // Public method to manually refresh indicators
    async refresh() {
        try {
            const response = await fetch('/api/ai/all-job-indicators');
            const data = await response.json();
            this.indicators = data.indicators || {};
            
            // Remove old indicators
            document.querySelectorAll('.ai-indicators-container').forEach(el => el.remove());
            
            this.applyJobIndicators();
        } catch (error) {
            console.error('Refresh indicators error:', error);
        }
    }

    // Add ghost overlay for AI recommendation
    addGhostOverlay(element, recommendation) {
        const ghost = document.createElement('div');
        ghost.className = 'ai-ghost-overlay';
        ghost.setAttribute('data-recommendation', JSON.stringify(recommendation));
        
        element.style.position = 'relative';
        element.appendChild(ghost);
        
        ghost.addEventListener('click', (e) => {
            e.stopPropagation();
            // Open draft approval dialog
            if (window.aiOperatorDrawer) {
                window.aiOperatorDrawer.open();
            }
        });
    }
}

// Auto-init
let aiInlineIndicators = null;

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        aiInlineIndicators = new AIInlineIndicators();
        window.aiInlineIndicators = aiInlineIndicators;
    });
} else {
    aiInlineIndicators = new AIInlineIndicators();
    window.aiInlineIndicators = aiInlineIndicators;
}
