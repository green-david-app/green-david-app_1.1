/**
 * GREEN DAVID - AI JOBS INTEGRATION
 * ==================================
 * Zakázka jako operační centrum s AI operátorem.
 * 
 * Funkce:
 * - AI Panel v detailu zakázky (rizika, blokátory, doporučení)
 * - Ghost plán (návrhy změn)
 * - Decision Shadow (auditní stopa)
 * - AI akce (Reschedule, Reassign, Material expedite, atd.)
 * - Real-time přepočet podle reality
 */

class AIJobsIntegration {
    constructor() {
        this.currentJobId = null;
        this.jobData = null;
        this.aiAnalysis = null;
        this.ghostPlans = [];
        this.isLoading = false;
        
        // AI Actions catalog - SVG icons
        this.aiActions = {
            reschedule: {
                id: 'reschedule',
                label: 'Přeplánovat',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
                description: 'Navrhnout nový termín dokončení',
                requiresApproval: true
            },
            reassign: {
                id: 'reassign',
                label: 'Přerozdělit tým',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
                description: 'Změnit přiřazení pracovníků',
                requiresApproval: true
            },
            material_expedite: {
                id: 'material_expedite',
                label: 'Urychlit materiál',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
                description: 'Objednat chybějící materiál',
                requiresApproval: true
            },
            scope_checkpoint: {
                id: 'scope_checkpoint',
                label: 'Kontrola rozsahu',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
                description: 'Ověřit rozsah práce s klientem',
                requiresApproval: false
            },
            cost_control: {
                id: 'cost_control',
                label: 'Kontrola nákladů',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
                description: 'Analyzovat překročení rozpočtu',
                requiresApproval: false
            },
            stagnation_nudge: {
                id: 'stagnation_nudge',
                label: 'Aktivovat zakázku',
                icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
                description: 'Nastartovat stagnující zakázku',
                requiresApproval: false
            }
        };
    }

    // =========================================================================
    // INITIALIZATION
    // =========================================================================

    init(jobId) {
        this.currentJobId = jobId;
        this.injectAIPanel();
        this.loadJobAnalysis();
        this.startRealTimeUpdates();
    }

    injectAIPanel() {
        // Find the job detail container
        const container = document.querySelector('.job-detail-container') || 
                         document.querySelector('.job-content') ||
                         document.querySelector('main');
        
        if (!container) {
            console.warn('AI Jobs: Container not found');
            return;
        }

        // Create AI Panel
        const aiPanel = document.createElement('div');
        aiPanel.id = 'ai-job-panel';
        aiPanel.className = 'ai-job-panel';
        aiPanel.innerHTML = this.renderAIPanelHTML();
        
        // Insert after job header or at the beginning
        const jobHeader = container.querySelector('.job-header');
        if (jobHeader && jobHeader.nextSibling) {
            jobHeader.parentNode.insertBefore(aiPanel, jobHeader.nextSibling);
        } else {
            container.insertBefore(aiPanel, container.firstChild);
        }

        // Inject styles
        this.injectStyles();
    }

    renderAIPanelHTML() {
        return `
            <div class="ai-panel-header" onclick="aiJobsIntegration.togglePanel()">
                <div class="ai-panel-title">
                    <span class="ai-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="20" height="20"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></span>
                    <span>AI Operátor</span>
                    <span class="ai-status-badge" id="ai-status-badge">Analyzuji...</span>
                </div>
                <div class="ai-panel-toggle">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="6 9 12 15 18 9"/>
                    </svg>
                </div>
            </div>
            
            <div class="ai-panel-content" id="ai-panel-content">
                <!-- Health Score -->
                <div class="ai-health-score" id="ai-health-score">
                    <div class="health-ring">
                        <svg viewBox="0 0 36 36">
                            <path class="health-ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                            <path class="health-ring-fill" id="health-ring-path" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                        </svg>
                        <div class="health-value" id="health-value">--</div>
                    </div>
                    <div class="health-label">Zdraví zakázky</div>
                </div>
                
                <!-- Risk Indicators -->
                <div class="ai-section">
                    <h4>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        Rizika & Blokátory
                    </h4>
                    <div class="ai-risks-list" id="ai-risks-list">
                        <div class="ai-loading">Načítám analýzu...</div>
                    </div>
                </div>
                
                <!-- AI Recommendations -->
                <div class="ai-section">
                    <h4>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
                        </svg>
                        Doporučené kroky
                    </h4>
                    <div class="ai-recommendations" id="ai-recommendations">
                        <div class="ai-loading">Generuji doporučení...</div>
                    </div>
                </div>
                
                <!-- Ghost Plans -->
                <div class="ai-section">
                    <h4>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                        Ghost plán
                        <span class="ghost-badge">návrhy</span>
                    </h4>
                    <div class="ai-ghost-plans" id="ai-ghost-plans">
                        <div class="ghost-empty">Žádné návrhy změn</div>
                    </div>
                </div>
                
                <!-- Quick Actions -->
                <div class="ai-section ai-actions-section">
                    <h4>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                        </svg>
                        AI Akce
                    </h4>
                    <div class="ai-quick-actions" id="ai-quick-actions">
                        ${this.renderQuickActions()}
                    </div>
                </div>
                
                <!-- Decision History -->
                <div class="ai-section ai-history-section">
                    <h4 onclick="aiJobsIntegration.toggleHistory()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                        </svg>
                        Historie rozhodnutí
                        <span class="toggle-icon">▼</span>
                    </h4>
                    <div class="ai-history-list" id="ai-history-list" style="display:none;">
                        <div class="ai-loading">Načítám historii...</div>
                    </div>
                </div>
            </div>
        `;
    }

    renderQuickActions() {
        let html = '<div class="quick-actions-grid">';
        
        for (const [key, action] of Object.entries(this.aiActions)) {
            html += `
                <button class="quick-action-btn" onclick="aiJobsIntegration.executeAction('${key}')" title="${action.description}">
                    <span class="action-icon">${action.icon}</span>
                    <span class="action-label">${action.label}</span>
                    ${action.requiresApproval ? '<span class="approval-badge">schválení</span>' : ''}
                </button>
            `;
        }
        
        html += '</div>';
        return html;
    }

    // =========================================================================
    // DATA LOADING
    // =========================================================================

    async loadJobAnalysis() {
        if (!this.currentJobId) return;
        
        this.isLoading = true;
        this.updateStatusBadge('loading');
        
        try {
            // Load multiple data sources in parallel
            const [risks, causal, probability, decisions] = await Promise.all([
                this.fetchRisks(),
                this.fetchCausalAnalysis(),
                this.fetchProbabilityMap(),
                this.fetchDecisionHistory()
            ]);
            
            this.aiAnalysis = {
                risks,
                causal,
                probability,
                decisions,
                loadedAt: new Date().toISOString()
            };
            
            this.renderAnalysis();
            this.calculateHealthScore();
            this.generateGhostPlans();
            
            this.updateStatusBadge('ready');
            
        } catch (error) {
            console.error('AI Analysis error:', error);
            this.updateStatusBadge('error');
        }
        
        this.isLoading = false;
    }

    async fetchRisks() {
        try {
            const response = await fetch(`/api/ai/risks/job/${this.currentJobId}`);
            const data = await response.json();
            return data.risks || [];
        } catch {
            return [];
        }
    }

    async fetchCausalAnalysis() {
        try {
            const response = await fetch(`/api/ai/causal/job/${this.currentJobId}`);
            return await response.json();
        } catch {
            return null;
        }
    }

    async fetchProbabilityMap() {
        try {
            const response = await fetch(`/api/ai/probability-map/job/${this.currentJobId}`);
            return await response.json();
        } catch {
            return null;
        }
    }

    async fetchDecisionHistory() {
        try {
            const response = await fetch(`/api/ai/decisions?entity_type=job&entity_id=${this.currentJobId}`);
            const data = await response.json();
            return data.decisions || [];
        } catch {
            return [];
        }
    }

    // =========================================================================
    // RENDERING
    // =========================================================================

    renderAnalysis() {
        this.renderRisks();
        this.renderRecommendations();
        this.renderDecisionHistory();
    }

    renderRisks() {
        const container = document.getElementById('ai-risks-list');
        if (!container) return;
        
        const risks = this.aiAnalysis?.risks || [];
        
        if (risks.length === 0) {
            container.innerHTML = '<div class="no-risks"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" style="color:#4ade80;vertical-align:middle;margin-right:6px;"><polyline points="20 6 9 17 4 12"/></svg>Žádná významná rizika</div>';
            return;
        }
        
        let html = '';
        risks.forEach(risk => {
            const severityClass = risk.severity || 'medium';
            const icon = this.getRiskIcon(risk.category || risk.type);
            
            html += `
                <div class="risk-item ${severityClass}">
                    <div class="risk-header">
                        <span class="risk-icon">${icon}</span>
                        <span class="risk-title">${risk.description || risk.type}</span>
                        <span class="risk-score">${risk.score || risk.probability * 100}%</span>
                    </div>
                    ${risk.mitigation ? `
                        <div class="risk-mitigation">
                            <strong>Mitigace:</strong>
                            <ul>
                                ${risk.mitigation.slice(0, 2).map(m => `<li>${m.description}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    getRiskIcon(category) {
        const icons = {
            'schedule': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
            'budget': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
            'resource': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
            'weather': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M20 17.58A5 5 0 0 0 18 8h-1.26A8 8 0 1 0 4 16.25"/><line x1="8" y1="16" x2="8" y2="20"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="16" y1="16" x2="16" y2="20"/></svg>',
            'material': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
            'quality': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><polyline points="20 6 9 17 4 12"/></svg>',
            'client': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><polyline points="17 11 19 13 23 9"/></svg>',
            'default': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
        };
        return icons[category] || icons.default;
    }

    renderRecommendations() {
        const container = document.getElementById('ai-recommendations');
        if (!container) return;
        
        const recommendations = this.generateRecommendations();
        
        if (recommendations.length === 0) {
            container.innerHTML = '<div class="no-recommendations"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16" style="color:#4ade80;vertical-align:middle;margin-right:6px;"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>Vše v pořádku</div>';
            return;
        }
        
        let html = '';
        recommendations.forEach((rec, index) => {
            html += `
                <div class="recommendation-item" data-priority="${rec.priority}">
                    <div class="rec-number">${index + 1}</div>
                    <div class="rec-content">
                        <div class="rec-title">${rec.title}</div>
                        <div class="rec-description">${rec.description}</div>
                    </div>
                    <button class="rec-action" onclick="aiJobsIntegration.executeRecommendation('${rec.action}')">
                        ${rec.actionLabel || 'Provést'}
                    </button>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    generateRecommendations() {
        const recommendations = [];
        const risks = this.aiAnalysis?.risks || [];
        const causal = this.aiAnalysis?.causal;
        const probability = this.aiAnalysis?.probability;
        
        // Based on risks
        risks.forEach(risk => {
            if (risk.severity === 'high') {
                if (risk.type === 'schedule_delay' || risk.category === 'schedule') {
                    recommendations.push({
                        title: 'Přeplánovat termín',
                        description: 'Zakázka má vysoké riziko zpoždění.',
                        action: 'reschedule',
                        actionLabel: 'Přeplánovat',
                        priority: 1
                    });
                }
                if (risk.type === 'budget_overrun' || risk.category === 'budget') {
                    recommendations.push({
                        title: 'Zkontrolovat náklady',
                        description: 'Rozpočet je překročen nebo se blíží limitu.',
                        action: 'cost_control',
                        actionLabel: 'Analyzovat',
                        priority: 1
                    });
                }
                if (risk.type === 'resource_shortage' || risk.category === 'resource') {
                    recommendations.push({
                        title: 'Přidat pracovníky',
                        description: 'Nedostatek kapacity pro dokončení včas.',
                        action: 'reassign',
                        actionLabel: 'Přerozdělit',
                        priority: 2
                    });
                }
            }
        });
        
        // Based on causal analysis
        if (causal?.root_cause) {
            if (causal.root_cause.type === 'missing_material') {
                recommendations.push({
                    title: 'Objednat materiál',
                    description: causal.root_cause.evidence || 'Chybí potřebný materiál.',
                    action: 'material_expedite',
                    actionLabel: 'Objednat',
                    priority: 1
                });
            }
        }
        
        // Based on probability
        if (probability?.trajectories) {
            const pessimistic = probability.trajectories.find(t => t.name === 'pessimistic');
            if (pessimistic && pessimistic.probability > 0.3) {
                recommendations.push({
                    title: 'Zvážit scope',
                    description: 'Vysoká pravděpodobnost komplikací - ověřte rozsah.',
                    action: 'scope_checkpoint',
                    actionLabel: 'Ověřit',
                    priority: 2
                });
            }
        }
        
        // Sort by priority
        return recommendations.sort((a, b) => a.priority - b.priority).slice(0, 5);
    }

    renderDecisionHistory() {
        const container = document.getElementById('ai-history-list');
        if (!container) return;
        
        const decisions = this.aiAnalysis?.decisions || [];
        
        if (decisions.length === 0) {
            container.innerHTML = '<div class="no-history">Žádná zaznamenaná rozhodnutí</div>';
            return;
        }
        
        let html = '<div class="decision-timeline">';
        decisions.slice(0, 10).forEach(decision => {
            const date = new Date(decision.created_at).toLocaleDateString('cs-CZ');
            const statusIcon = decision.approval_status === 'approved' ? '✓' : 
                              decision.approval_status === 'rejected' ? '✗' : '○';
            
            html += `
                <div class="decision-item ${decision.approval_status || 'pending'}">
                    <div class="decision-marker">${statusIcon}</div>
                    <div class="decision-content">
                        <div class="decision-title">${decision.title}</div>
                        <div class="decision-meta">${date} · ${decision.decision_type}</div>
                        ${decision.outcome ? `<div class="decision-outcome">Výsledek: ${decision.outcome}</div>` : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
        
        container.innerHTML = html;
    }

    // =========================================================================
    // HEALTH SCORE
    // =========================================================================

    calculateHealthScore() {
        let score = 100;
        const risks = this.aiAnalysis?.risks || [];
        
        // Subtract for risks
        risks.forEach(risk => {
            if (risk.severity === 'high') score -= 20;
            else if (risk.severity === 'medium') score -= 10;
            else score -= 5;
        });
        
        // Adjust based on probability
        const probability = this.aiAnalysis?.probability;
        if (probability?.trajectories) {
            const pessimistic = probability.trajectories.find(t => t.name === 'pessimistic');
            if (pessimistic && pessimistic.probability > 0.3) {
                score -= 10;
            }
        }
        
        score = Math.max(0, Math.min(100, score));
        
        this.renderHealthScore(score);
    }

    renderHealthScore(score) {
        const valueEl = document.getElementById('health-value');
        const pathEl = document.getElementById('health-ring-path');
        
        if (valueEl) {
            valueEl.textContent = score;
            valueEl.className = 'health-value ' + this.getHealthClass(score);
        }
        
        if (pathEl) {
            pathEl.setAttribute('stroke-dasharray', `${score}, 100`);
            pathEl.className = 'health-ring-fill ' + this.getHealthClass(score);
        }
    }

    getHealthClass(score) {
        if (score >= 80) return 'health-good';
        if (score >= 50) return 'health-warning';
        return 'health-danger';
    }

    // =========================================================================
    // GHOST PLANS
    // =========================================================================

    generateGhostPlans() {
        this.ghostPlans = [];
        const risks = this.aiAnalysis?.risks || [];
        const probability = this.aiAnalysis?.probability;
        
        // Generate ghost plan based on risks
        risks.forEach(risk => {
            if (risk.severity === 'high' && risk.mitigation?.length > 0) {
                const mitigation = risk.mitigation[0];
                this.ghostPlans.push({
                    id: `ghost_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    type: mitigation.action,
                    title: mitigation.description,
                    impact: `Snížení rizika: ${risk.type}`,
                    cost: mitigation.cost,
                    confidence: 70,
                    status: 'proposed'
                });
            }
        });
        
        // Ghost plan based on deadline
        if (probability?.confidence_interval) {
            const upper = new Date(probability.confidence_interval.upper);
            const deadline = this.jobData?.planned_end_date ? new Date(this.jobData.planned_end_date) : null;
            
            if (deadline && upper > deadline) {
                const daysDiff = Math.ceil((upper - deadline) / (1000 * 60 * 60 * 24));
                this.ghostPlans.push({
                    id: `ghost_deadline_${Date.now()}`,
                    type: 'reschedule',
                    title: `Posunout deadline o ${daysDiff} dní`,
                    impact: 'Realističtější termín dokončení',
                    newDeadline: upper.toISOString().split('T')[0],
                    confidence: 60,
                    status: 'proposed'
                });
            }
        }
        
        this.renderGhostPlans();
    }

    renderGhostPlans() {
        const container = document.getElementById('ai-ghost-plans');
        if (!container) return;
        
        if (this.ghostPlans.length === 0) {
            container.innerHTML = '<div class="ghost-empty">Žádné návrhy změn</div>';
            return;
        }
        
        let html = '';
        this.ghostPlans.forEach(plan => {
            html += `
                <div class="ghost-plan-item" data-id="${plan.id}">
                    <div class="ghost-icon">👻</div>
                    <div class="ghost-content">
                        <div class="ghost-title">${plan.title}</div>
                        <div class="ghost-impact">${plan.impact}</div>
                        <div class="ghost-confidence">Důvěra: ${plan.confidence}%</div>
                    </div>
                    <div class="ghost-actions">
                        <button class="ghost-approve" onclick="aiJobsIntegration.approveGhostPlan('${plan.id}')" title="Schválit">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg>
                        </button>
                        <button class="ghost-reject" onclick="aiJobsIntegration.rejectGhostPlan('${plan.id}')" title="Zamítnout">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" width="14" height="14"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                        </button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    async approveGhostPlan(planId) {
        const plan = this.ghostPlans.find(p => p.id === planId);
        if (!plan) return;
        
        // Create decision shadow
        await this.createDecisionShadow({
            type: plan.type,
            title: plan.title,
            reasoning: `Ghost plán schválen. ${plan.impact}`,
            chosen: plan.title,
            confidence: plan.confidence
        });
        
        // Create draft action
        await this.createDraftAction(plan);
        
        // Remove from ghost plans
        this.ghostPlans = this.ghostPlans.filter(p => p.id !== planId);
        this.renderGhostPlans();
        
        this.showToast('Ghost plán schválen - vytvořen draft k realizaci', 'success');
    }

    async rejectGhostPlan(planId) {
        const plan = this.ghostPlans.find(p => p.id === planId);
        if (!plan) return;
        
        // Log rejection
        await this.createDecisionShadow({
            type: plan.type,
            title: `Zamítnuto: ${plan.title}`,
            reasoning: 'Ghost plán zamítnut uživatelem',
            chosen: 'reject',
            confidence: 100
        });
        
        // Remove from ghost plans
        this.ghostPlans = this.ghostPlans.filter(p => p.id !== planId);
        this.renderGhostPlans();
        
        this.showToast('Ghost plán zamítnut', 'info');
    }

    // =========================================================================
    // AI ACTIONS
    // =========================================================================

    async executeAction(actionKey) {
        const action = this.aiActions[actionKey];
        if (!action) return;
        
        // Show confirmation for actions requiring approval
        if (action.requiresApproval) {
            const confirmed = confirm(`${action.label}\n\n${action.description}\n\nTato akce vyžaduje schválení. Vytvořit návrh?`);
            if (!confirmed) return;
        }
        
        // Execute action
        switch (actionKey) {
            case 'reschedule':
                await this.actionReschedule();
                break;
            case 'reassign':
                await this.actionReassign();
                break;
            case 'material_expedite':
                await this.actionMaterialExpedite();
                break;
            case 'scope_checkpoint':
                await this.actionScopeCheckpoint();
                break;
            case 'cost_control':
                await this.actionCostControl();
                break;
            case 'stagnation_nudge':
                await this.actionStagnationNudge();
                break;
        }
    }

    async executeRecommendation(action) {
        await this.executeAction(action);
    }

    async actionReschedule() {
        // Get probability-based suggestion
        const probability = this.aiAnalysis?.probability;
        let suggestedDate = null;
        
        if (probability?.trajectories) {
            const realistic = probability.trajectories.find(t => t.name === 'realistic');
            if (realistic?.completion_date) {
                suggestedDate = realistic.completion_date;
            }
        }
        
        const newDate = prompt(
            'Nový termín dokončení (YYYY-MM-DD):',
            suggestedDate || ''
        );
        
        if (!newDate) return;
        
        await this.createDraftAction({
            type: 'reschedule',
            title: `Přeplánovat zakázku na ${newDate}`,
            payload: { new_deadline: newDate }
        });
        
        await this.createDecisionShadow({
            type: 'reschedule',
            title: 'Změna termínu zakázky',
            reasoning: 'Přeplánování na základě AI analýzy',
            chosen: newDate,
            confidence: 70
        });
        
        this.showToast('Návrh přeplánování vytvořen', 'success');
    }

    async actionReassign() {
        // Get available workers
        try {
            const response = await fetch(`/api/ai/constraints/workers/${this.currentJobId}?date=${new Date().toISOString().split('T')[0]}`);
            const data = await response.json();
            
            const available = (data.workers || []).filter(w => w.available);
            
            if (available.length === 0) {
                this.showToast('Žádní dostupní pracovníci', 'warning');
                return;
            }
            
            const workerList = available.map(w => `${w.name} (${w.remaining_weekly}h volných)`).join('\n');
            const selected = prompt(`Dostupní pracovníci:\n${workerList}\n\nZadejte jméno:`);
            
            if (!selected) return;
            
            await this.createDraftAction({
                type: 'reassign',
                title: `Přiřadit: ${selected}`,
                payload: { worker_name: selected }
            });
            
            this.showToast('Návrh přiřazení vytvořen', 'success');
            
        } catch (error) {
            this.showToast('Chyba při načítání pracovníků', 'error');
        }
    }

    async actionMaterialExpedite() {
        // Check for missing materials from causal analysis
        const causal = this.aiAnalysis?.causal;
        let materials = [];
        
        if (causal?.causes) {
            const materialCause = causal.causes.find(c => c.type === 'missing_material');
            if (materialCause?.items) {
                materials = materialCause.items;
            }
        }
        
        if (materials.length > 0) {
            const materialList = materials.map(m => `${m.name}: chybí ${m.reserved - m.available}`).join('\n');
            
            await this.createDraftAction({
                type: 'material_expedite',
                title: 'Objednat chybějící materiál',
                payload: { materials }
            });
            
            this.showToast(`Návrh objednávky vytvořen\n${materials.length} položek`, 'success');
        } else {
            this.showToast('Žádný chybějící materiál detekován', 'info');
        }
    }

    async actionScopeCheckpoint() {
        // Open scope review
        await this.createDecisionShadow({
            type: 'scope_checkpoint',
            title: 'Kontrola rozsahu zakázky',
            reasoning: 'Periodická kontrola rozsahu na základě AI doporučení',
            chosen: 'initiated',
            confidence: 90
        });
        
        this.showToast('Kontrola rozsahu zahájena - kontaktujte klienta', 'info');
    }

    async actionCostControl() {
        // Analyze costs
        const risks = this.aiAnalysis?.risks || [];
        const budgetRisk = risks.find(r => r.category === 'budget' || r.type === 'budget_overrun');
        
        let message = 'Analýza nákladů:\n';
        
        if (budgetRisk) {
            message += `\n⚠️ ${budgetRisk.description}`;
            if (budgetRisk.mitigation) {
                message += '\n\nDoporučené kroky:';
                budgetRisk.mitigation.forEach(m => {
                    message += `\n- ${m.description}`;
                });
            }
        } else {
            message += '\n✓ Náklady jsou v normě';
        }
        
        alert(message);
        
        await this.createDecisionShadow({
            type: 'cost_control',
            title: 'Kontrola nákladů',
            reasoning: 'Analýza rozpočtu zakázky',
            chosen: budgetRisk ? 'warning' : 'ok',
            confidence: 80
        });
    }

    async actionStagnationNudge() {
        await this.createDraftAction({
            type: 'stagnation_nudge',
            title: 'Aktivovat stagnující zakázku',
            payload: { 
                actions: ['schedule_meeting', 'assign_priority', 'check_blockers']
            }
        });
        
        await this.createDecisionShadow({
            type: 'stagnation_nudge',
            title: 'Aktivace stagnující zakázky',
            reasoning: 'Zakázka bez aktivity - aktivační kroky',
            chosen: 'nudge',
            confidence: 75
        });
        
        this.showToast('Aktivační kroky naplánovány', 'success');
    }

    // =========================================================================
    // API HELPERS
    // =========================================================================

    async createDraftAction(plan) {
        try {
            await fetch('/api/ai/drafts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    insight_id: `job_${this.currentJobId}_${plan.type}`,
                    type: plan.type,
                    title: plan.title,
                    entity: 'job',
                    entity_id: this.currentJobId,
                    payload: plan.payload || {}
                })
            });
        } catch (error) {
            console.error('Create draft error:', error);
        }
    }

    async createDecisionShadow(decision) {
        try {
            await fetch('/api/ai/decision-shadow', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: decision.type,
                    user_id: 1, // TODO: Get actual user
                    chosen: decision.chosen,
                    reasoning: decision.reasoning,
                    context: {
                        job_id: this.currentJobId,
                        timestamp: new Date().toISOString()
                    },
                    confidence: decision.confidence,
                    entity_type: 'job',
                    entity_id: this.currentJobId
                })
            });
        } catch (error) {
            console.error('Decision shadow error:', error);
        }
    }

    // =========================================================================
    // UI HELPERS
    // =========================================================================

    togglePanel() {
        const content = document.getElementById('ai-panel-content');
        const panel = document.getElementById('ai-job-panel');
        
        if (content) {
            content.classList.toggle('collapsed');
            panel?.classList.toggle('collapsed');
        }
    }

    toggleHistory() {
        const historyList = document.getElementById('ai-history-list');
        if (historyList) {
            historyList.style.display = historyList.style.display === 'none' ? 'block' : 'none';
        }
    }

    updateStatusBadge(status) {
        const badge = document.getElementById('ai-status-badge');
        if (!badge) return;
        
        const statuses = {
            'loading': { text: 'Analyzuji...', class: 'loading' },
            'ready': { text: 'Připraven', class: 'ready' },
            'error': { text: 'Chyba', class: 'error' }
        };
        
        const s = statuses[status] || statuses.ready;
        badge.textContent = s.text;
        badge.className = 'ai-status-badge ' + s.class;
    }

    showToast(message, type = 'info') {
        // Use existing toast system or create simple one
        if (window.showToast) {
            window.showToast(message, type);
            return;
        }
        
        const toast = document.createElement('div');
        toast.className = `ai-toast ai-toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.classList.add('show'), 10);
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    startRealTimeUpdates() {
        // Refresh every 5 minutes
        setInterval(() => {
            if (!this.isLoading) {
                this.loadJobAnalysis();
            }
        }, 5 * 60 * 1000);
    }

    // =========================================================================
    // STYLES
    // =========================================================================

    injectStyles() {
        if (document.getElementById('ai-jobs-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'ai-jobs-styles';
        style.textContent = `
            /* AI Job Panel */
            .ai-job-panel {
                background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
                border: 1px solid #3d4556;
                border-radius: 12px;
                margin-bottom: 16px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            
            .ai-job-panel.collapsed .ai-panel-content {
                display: none;
            }
            
            .ai-panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 16px;
                background: rgba(167, 139, 250, 0.1);
                cursor: pointer;
                border-bottom: 1px solid #3d4556;
            }
            
            .ai-panel-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                color: #a78bfa;
            }
            
            .ai-icon {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .ai-icon svg {
                stroke: #a78bfa;
            }
            
            .ai-status-badge {
                font-size: 11px;
                padding: 3px 8px;
                border-radius: 10px;
                background: rgba(255,255,255,0.1);
            }
            
            .ai-status-badge.loading { color: #fbbf24; }
            .ai-status-badge.ready { color: #4ade80; }
            .ai-status-badge.error { color: #f87171; }
            
            .ai-panel-toggle {
                color: #64748b;
                transition: transform 0.2s;
            }
            
            .ai-job-panel.collapsed .ai-panel-toggle {
                transform: rotate(-90deg);
            }
            
            .ai-panel-content {
                padding: 16px;
            }
            
            .ai-panel-content.collapsed {
                display: none;
            }
            
            /* Health Score */
            .ai-health-score {
                display: flex;
                flex-direction: column;
                align-items: center;
                margin-bottom: 20px;
            }
            
            .health-ring {
                position: relative;
                width: 100px;
                height: 100px;
            }
            
            .health-ring svg {
                transform: rotate(-90deg);
            }
            
            .health-ring-bg {
                fill: none;
                stroke: #2d3748;
                stroke-width: 3;
            }
            
            .health-ring-fill {
                fill: none;
                stroke-width: 3;
                stroke-linecap: round;
                transition: stroke-dasharray 0.5s ease;
            }
            
            .health-ring-fill.health-good { stroke: #4ade80; }
            .health-ring-fill.health-warning { stroke: #fbbf24; }
            .health-ring-fill.health-danger { stroke: #f87171; }
            
            .health-value {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 28px;
                font-weight: 700;
            }
            
            .health-value.health-good { color: #4ade80; }
            .health-value.health-warning { color: #fbbf24; }
            .health-value.health-danger { color: #f87171; }
            
            .health-label {
                margin-top: 8px;
                font-size: 12px;
                color: #64748b;
            }
            
            /* Sections */
            .ai-section {
                margin-bottom: 16px;
            }
            
            .ai-section h4 {
                display: flex;
                align-items: center;
                gap: 8px;
                margin: 0 0 10px 0;
                font-size: 13px;
                color: #94a3b8;
                cursor: pointer;
            }
            
            .ai-section h4 svg {
                stroke: #64748b;
                flex-shrink: 0;
            }
            
            .ghost-badge {
                font-size: 10px;
                padding: 2px 6px;
                background: rgba(167, 139, 250, 0.2);
                color: #a78bfa;
                border-radius: 8px;
                margin-left: auto;
            }
            
            /* Risks */
            .risk-item {
                background: rgba(255,255,255,0.03);
                border-radius: 8px;
                padding: 10px 12px;
                margin-bottom: 6px;
                border-left: 3px solid #64748b;
            }
            
            .risk-item.high { border-left-color: #f87171; }
            .risk-item.medium { border-left-color: #fbbf24; }
            .risk-item.low { border-left-color: #4ade80; }
            
            .risk-header {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .risk-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .risk-icon svg {
                stroke: currentColor;
            }
            
            .risk-title {
                flex: 1;
                font-size: 13px;
                color: #e2e8f0;
            }
            
            .risk-score {
                font-size: 12px;
                color: #64748b;
            }
            
            .risk-mitigation {
                margin-top: 8px;
                font-size: 12px;
                color: #94a3b8;
            }
            
            .risk-mitigation ul {
                margin: 4px 0 0 16px;
                padding: 0;
            }
            
            .no-risks, .no-recommendations, .ghost-empty, .no-history {
                text-align: center;
                padding: 20px;
                color: #64748b;
                font-size: 13px;
            }
            
            /* Recommendations */
            .recommendation-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: rgba(255,255,255,0.03);
                border-radius: 8px;
                margin-bottom: 8px;
            }
            
            .rec-number {
                width: 24px;
                height: 24px;
                border-radius: 50%;
                background: rgba(167, 139, 250, 0.2);
                color: #a78bfa;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: 600;
            }
            
            .rec-content {
                flex: 1;
            }
            
            .rec-title {
                font-size: 13px;
                color: #e2e8f0;
                font-weight: 500;
            }
            
            .rec-description {
                font-size: 11px;
                color: #64748b;
                margin-top: 2px;
            }
            
            .rec-action {
                padding: 6px 12px;
                background: rgba(167, 139, 250, 0.2);
                border: none;
                border-radius: 6px;
                color: #a78bfa;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .rec-action:hover {
                background: rgba(167, 139, 250, 0.3);
            }
            
            /* Ghost Plans */
            .ghost-plan-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px;
                background: rgba(167, 139, 250, 0.05);
                border: 1px dashed rgba(167, 139, 250, 0.3);
                border-radius: 8px;
                margin-bottom: 8px;
            }
            
            .ghost-icon {
                font-size: 20px;
                opacity: 0.7;
            }
            
            .ghost-content {
                flex: 1;
            }
            
            .ghost-title {
                font-size: 13px;
                color: #e2e8f0;
            }
            
            .ghost-impact {
                font-size: 11px;
                color: #a78bfa;
                margin-top: 2px;
            }
            
            .ghost-confidence {
                font-size: 10px;
                color: #64748b;
                margin-top: 2px;
            }
            
            .ghost-actions {
                display: flex;
                gap: 6px;
            }
            
            .ghost-approve, .ghost-reject {
                width: 32px;
                height: 32px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .ghost-approve {
                background: rgba(74, 222, 128, 0.2);
            }
            
            .ghost-approve svg {
                stroke: #4ade80;
            }
            
            .ghost-approve:hover {
                background: rgba(74, 222, 128, 0.3);
            }
            
            .ghost-reject {
                background: rgba(248, 113, 113, 0.2);
            }
            
            .ghost-reject svg {
                stroke: #f87171;
            }
            
            .ghost-reject:hover {
                background: rgba(248, 113, 113, 0.3);
            }
            
            /* Quick Actions */
            .quick-actions-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
            }
            
            @media (max-width: 600px) {
                .quick-actions-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }
            
            .quick-action-btn {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 6px;
                padding: 14px 10px;
                background: rgba(255,255,255,0.03);
                border: 1px solid #3d4556;
                border-radius: 10px;
                color: #94a3b8;
                cursor: pointer;
                transition: all 0.2s;
                position: relative;
                min-height: 70px;
            }
            
            .quick-action-btn:hover {
                background: rgba(167, 139, 250, 0.1);
                border-color: #a78bfa;
                color: #e2e8f0;
            }
            
            .quick-action-btn:hover .action-icon svg {
                stroke: #a78bfa;
            }
            
            .action-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 24px;
                height: 24px;
            }
            
            .action-icon svg {
                stroke: currentColor;
                transition: stroke 0.2s;
            }
            
            .action-label {
                font-size: 11px;
                text-align: center;
                line-height: 1.3;
            }
            
            .approval-badge {
                position: absolute;
                top: 4px;
                right: 4px;
                font-size: 8px;
                padding: 2px 5px;
                background: rgba(251, 191, 36, 0.2);
                color: #fbbf24;
                border-radius: 4px;
            }
            
            /* Decision History */
            .decision-timeline {
                position: relative;
                padding-left: 20px;
            }
            
            .decision-timeline::before {
                content: '';
                position: absolute;
                left: 6px;
                top: 0;
                bottom: 0;
                width: 2px;
                background: #3d4556;
            }
            
            .decision-item {
                position: relative;
                padding: 10px 0;
            }
            
            .decision-marker {
                position: absolute;
                left: -20px;
                top: 12px;
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: #2d3748;
                border: 2px solid #3d4556;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 8px;
            }
            
            .decision-item.approved .decision-marker {
                background: #4ade80;
                border-color: #4ade80;
                color: #1a2332;
            }
            
            .decision-item.rejected .decision-marker {
                background: #f87171;
                border-color: #f87171;
                color: #1a2332;
            }
            
            .decision-title {
                font-size: 13px;
                color: #e2e8f0;
            }
            
            .decision-meta {
                font-size: 11px;
                color: #64748b;
                margin-top: 2px;
            }
            
            .decision-outcome {
                font-size: 11px;
                color: #94a3b8;
                margin-top: 4px;
                font-style: italic;
            }
            
            /* Toast */
            .ai-toast {
                position: fixed;
                bottom: 20px;
                right: 20px;
                padding: 12px 20px;
                background: #2d3748;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 14px;
                z-index: 10000;
                transform: translateY(100px);
                opacity: 0;
                transition: all 0.3s;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }
            
            .ai-toast.show {
                transform: translateY(0);
                opacity: 1;
            }
            
            .ai-toast-success {
                border-left: 3px solid #4ade80;
            }
            
            .ai-toast-warning {
                border-left: 3px solid #fbbf24;
            }
            
            .ai-toast-error {
                border-left: 3px solid #f87171;
            }
            
            .ai-toast-info {
                border-left: 3px solid #60a5fa;
            }
            
            .ai-loading {
                text-align: center;
                padding: 20px;
                color: #64748b;
            }
            
            .toggle-icon {
                margin-left: auto;
                font-size: 10px;
                transition: transform 0.2s;
            }
        `;
        
        document.head.appendChild(style);
    }
}

// Global instance
const aiJobsIntegration = new AIJobsIntegration();

// Auto-init on job detail pages
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on job detail page
    const urlParams = new URLSearchParams(window.location.search);
    const jobId = urlParams.get('id');
    
    if (jobId && (window.location.pathname.includes('job-detail') || 
                  window.location.pathname.includes('job_detail'))) {
        aiJobsIntegration.init(parseInt(jobId));
    }
});

// Export for manual use
window.aiJobsIntegration = aiJobsIntegration;
