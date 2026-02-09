/**
 * Smart Morning Planner
 * AI-powered ranní přehled a doporučení
 */

class SmartPlanner {
    constructor() {
        this.data = {
            jobs: [],
            tasks: [],
            employees: [],
            weather: null,
            warehouseAlerts: []
        };
    }
    
    async loadData() {
        try {
            const [jobs, tasks, employees, weather, warehouse] = await Promise.all([
                fetch('/api/jobs').then(r => r.json()).catch(() => []),
                fetch('/api/tasks').then(r => r.json()).catch(() => []),
                fetch('/api/employees').then(r => r.json()).catch(() => []),
                fetch('/api/weather').then(r => r.json()).catch(() => null),
                fetch('/api/warehouse/items?low_stock=1').then(r => r.json()).catch(() => [])
            ]);
            
            this.data.jobs = Array.isArray(jobs) ? jobs : (jobs.jobs || []);
            this.data.tasks = Array.isArray(tasks) ? tasks : (tasks.tasks || []);
            this.data.employees = Array.isArray(employees) ? employees : (employees.employees || []);
            this.data.weather = weather;
            this.data.warehouseAlerts = Array.isArray(warehouse) ? warehouse : (warehouse.items || []);
            
        } catch (e) {
            console.error('Error loading planner data:', e);
        }
    }
    
    async generatePlan() {
        await this.loadData();
        
        const today = new Date();
        const todayStr = today.toISOString().split('T')[0];
        const dayName = today.toLocaleDateString('cs-CZ', { weekday: 'long' });
        
        // Analyze data
        const analysis = this.analyzeData(todayStr);
        
        return {
            date: todayStr,
            dayName: dayName,
            greeting: this.getGreeting(),
            weather: this.getWeatherSummary(),
            weatherWarning: this.getWeatherWarning(),
            todaysTasks: analysis.todaysTasks,
            urgentTasks: analysis.urgentTasks,
            activeJobs: analysis.activeJobs,
            teamRecommendations: this.generateTeamRecommendations(analysis),
            warnings: analysis.warnings,
            suggestions: this.generateSuggestions(analysis),
            score: this.calculateDayScore(analysis)
        };
    }
    
    getGreeting() {
        const hour = new Date().getHours();
        if (hour < 9) return 'Dobré ráno! ☀️';
        if (hour < 12) return 'Dopolední přehled 📋';
        if (hour < 18) return 'Odpolední přehled 📋';
        return 'Večerní přehled 🌙';
    }
    
    analyzeData(todayStr) {
        const analysis = {
            todaysTasks: [],
            urgentTasks: [],
            activeJobs: [],
            overdueTasks: [],
            upcomingDeadlines: [],
            warnings: []
        };
        
        // Tasks analysis
        this.data.tasks.forEach(task => {
            if (task.status === 'done') return;
            
            if (task.deadline === todayStr) {
                analysis.todaysTasks.push(task);
            }
            
            if (task.priority === 'urgent') {
                analysis.urgentTasks.push(task);
            }
            
            if (task.deadline && task.deadline < todayStr) {
                analysis.overdueTasks.push(task);
            }
            
            // Upcoming 3 days
            if (task.deadline) {
                const deadline = new Date(task.deadline);
                const diffDays = Math.ceil((deadline - new Date()) / (1000 * 60 * 60 * 24));
                if (diffDays > 0 && diffDays <= 3) {
                    analysis.upcomingDeadlines.push({ ...task, daysUntil: diffDays });
                }
            }
        });
        
        // Jobs analysis
        this.data.jobs.forEach(job => {
            if (job.status === 'active' || job.status === 'in_progress') {
                analysis.activeJobs.push(job);
            }
        });
        
        // Warnings
        if (analysis.overdueTasks.length > 0) {
            analysis.warnings.push({
                type: 'overdue',
                severity: 'high',
                message: `${analysis.overdueTasks.length} úkolů po termínu!`,
                items: analysis.overdueTasks
            });
        }
        
        if (this.data.warehouseAlerts && this.data.warehouseAlerts.length > 0) {
            analysis.warnings.push({
                type: 'lowStock',
                severity: 'medium',
                message: `${this.data.warehouseAlerts.length} položek má nízké zásoby`,
                items: this.data.warehouseAlerts
            });
        }
        
        return analysis;
    }
    
    getWeatherSummary() {
        if (!this.data.weather?.current) return null;
        
        const w = this.data.weather;
        return {
            temperature: Math.round(w.current.temperature),
            description: w.current.description || '',
            icon: w.current.icon || '☀️',
            city: w.city || 'Příbram'
        };
    }
    
    getWeatherWarning() {
        if (!this.data.weather?.current) return null;
        
        const temp = this.data.weather.current.temperature;
        const condition = (this.data.weather.current.condition || '').toLowerCase();
        
        const warnings = [];
        
        if (condition.includes('rain') || condition.includes('déšť') || condition.includes('bouřka')) {
            warnings.push({
                type: 'rain',
                icon: '🌧️',
                message: 'Očekává se déšť - zvažte plánování venkovních prací'
            });
        }
        
        if (temp < 5) {
            warnings.push({
                type: 'cold',
                icon: '🥶',
                message: `Nízká teplota (${Math.round(temp)}°C) - zajistěte teplé oblečení`
            });
        }
        
        if (temp > 30) {
            warnings.push({
                type: 'heat',
                icon: '🥵',
                message: `Vysoká teplota (${Math.round(temp)}°C) - dbejte na pitný režim`
            });
        }
        
        return warnings.length > 0 ? warnings : null;
    }
    
    generateTeamRecommendations(analysis) {
        const recommendations = [];
        const availableEmployees = this.data.employees.filter(e => e.status !== 'inactive');
        
        // Simple assignment logic
        analysis.activeJobs.forEach((job, index) => {
            if (index < availableEmployees.length) {
                recommendations.push({
                    employee: availableEmployees[index],
                    job: job,
                    reason: job.address ? `Nejbližší k ${job.address.split(',')[0]}` : 'Volná kapacita'
                });
            }
        });
        
        return recommendations;
    }
    
    generateSuggestions(analysis) {
        const suggestions = [];
        
        // Priority suggestions
        if (analysis.urgentTasks.length > 0) {
            suggestions.push({
                icon: '🚨',
                text: `Začni s urgentními úkoly (${analysis.urgentTasks.length})`,
                action: 'tasks.html?filter=urgent'
            });
        }
        
        if (analysis.overdueTasks.length > 0) {
            suggestions.push({
                icon: '⏰',
                text: `Vyřeš ${analysis.overdueTasks.length} prošlých úkolů`,
                action: 'tasks.html?filter=overdue'
            });
        }
        
        // Weather-based suggestions
        if (this.getWeatherWarning()?.some(w => w.type === 'rain')) {
            suggestions.push({
                icon: '🏠',
                text: 'Naplánuj vnitřní práce kvůli dešti',
                action: null
            });
        }
        
        // Capacity suggestions
        const pendingTasks = this.data.tasks.filter(t => t.status !== 'done').length;
        const activeJobs = analysis.activeJobs.length;
        
        if (pendingTasks > 20) {
            suggestions.push({
                icon: '📊',
                text: 'Hodně úkolů - zvažte delegování nebo přehodnocení priorit',
                action: 'tasks.html'
            });
        }
        
        if (activeJobs > 5) {
            suggestions.push({
                icon: '📋',
                text: `${activeJobs} aktivních zakázek - zkontroluj progress`,
                action: 'jobs.html?filter=active'
            });
        }
        
        // Proactive suggestions
        if (analysis.upcomingDeadlines.length > 0) {
            const tomorrow = analysis.upcomingDeadlines.filter(t => t.daysUntil === 1);
            if (tomorrow.length > 0) {
                suggestions.push({
                    icon: '📅',
                    text: `${tomorrow.length} úkolů má deadline zítra`,
                    action: 'tasks.html'
                });
            }
        }
        
        return suggestions;
    }
    
    calculateDayScore(analysis) {
        let score = 100;
        
        // Deductions
        score -= analysis.overdueTasks.length * 10;
        score -= analysis.urgentTasks.length * 5;
        score -= this.data.warehouseAlerts.length * 2;
        
        // Weather impact
        if (this.getWeatherWarning()) {
            score -= 5;
        }
        
        // Bonuses
        if (analysis.todaysTasks.length < 5) {
            score += 5; // Manageable workload
        }
        
        return Math.max(0, Math.min(100, score));
    }
    
    // Render the planner UI
    async render(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = '<div class="planner-loading">Připravuji ranní přehled...</div>';
        
        const plan = await this.generatePlan();
        
        container.innerHTML = `
            <div class="smart-planner">
                <div class="planner-header">
                    <div class="planner-greeting">
                        <h2>${plan.greeting}</h2>
                        <p>${plan.dayName}, ${new Date().toLocaleDateString('cs-CZ')}</p>
                    </div>
                    <div class="planner-score">
                        <div class="score-circle ${plan.score > 70 ? 'good' : plan.score > 40 ? 'medium' : 'bad'}">
                            ${plan.score}
                        </div>
                        <span>Skóre dne</span>
                    </div>
                </div>
                
                ${plan.weather ? `
                <div class="planner-weather">
                    <span class="weather-icon">${plan.weather.icon}</span>
                    <span class="weather-temp">${plan.weather.temperature}°C</span>
                    <span class="weather-desc">${plan.weather.description}</span>
                </div>
                ` : ''}
                
                ${plan.weatherWarning ? `
                <div class="planner-warnings weather-warnings">
                    ${plan.weatherWarning.map(w => `
                        <div class="warning-item weather">
                            <span class="warning-icon">${w.icon}</span>
                            <span>${w.message}</span>
                        </div>
                    `).join('')}
                </div>
                ` : ''}
                
                ${plan.warnings.length > 0 ? `
                <div class="planner-warnings">
                    ${plan.warnings.map(w => `
                        <div class="warning-item ${w.severity}">
                            <span class="warning-icon">${w.severity === 'high' ? '🚨' : '⚠️'}</span>
                            <span>${w.message}</span>
                        </div>
                    `).join('')}
                </div>
                ` : ''}
                
                <div class="planner-section">
                    <h3>📋 Dnešní úkoly (${plan.todaysTasks.length})</h3>
                    ${plan.todaysTasks.length > 0 ? `
                        <div class="task-list">
                            ${plan.todaysTasks.slice(0, 5).map(t => `
                                <div class="task-item ${t.priority === 'urgent' ? 'urgent' : ''}">
                                    <span class="task-priority">${t.priority === 'urgent' ? '🔴' : '🔵'}</span>
                                    <span class="task-title">${t.title}</span>
                                </div>
                            `).join('')}
                            ${plan.todaysTasks.length > 5 ? `<p class="more">+${plan.todaysTasks.length - 5} dalších</p>` : ''}
                        </div>
                    ` : '<p class="empty">Žádné úkoly na dnes 🎉</p>'}
                </div>
                
                ${plan.urgentTasks.length > 0 ? `
                <div class="planner-section urgent">
                    <h3>🚨 Urgentní (${plan.urgentTasks.length})</h3>
                    <div class="task-list">
                        ${plan.urgentTasks.slice(0, 3).map(t => `
                            <div class="task-item urgent">
                                <span class="task-title">${t.title}</span>
                                ${t.deadline ? `<span class="task-deadline">${t.deadline}</span>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${plan.teamRecommendations.length > 0 ? `
                <div class="planner-section">
                    <h3>👥 Doporučené přiřazení</h3>
                    <div class="team-recommendations">
                        ${plan.teamRecommendations.map(r => `
                            <div class="recommendation-item">
                                <div class="rec-employee">👤 ${r.employee.name || r.employee.email}</div>
                                <div class="rec-arrow">→</div>
                                <div class="rec-job">📋 ${r.job.client || r.job.name}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${plan.suggestions.length > 0 ? `
                <div class="planner-section">
                    <h3>💡 Doporučení</h3>
                    <div class="suggestions-list">
                        ${plan.suggestions.map(s => `
                            <div class="suggestion-item" ${s.action ? `onclick="window.location.href='/${s.action}'"` : ''}>
                                <span class="suggestion-icon">${s.icon}</span>
                                <span>${s.text}</span>
                                ${s.action ? '<span class="suggestion-arrow">→</span>' : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
                ` : ''}
                
                <div class="planner-actions">
                    <button onclick="window.location.href='/tasks.html'" class="planner-btn primary">
                        Zobrazit úkoly
                    </button>
                    <button onclick="window.location.href='/timeline'" class="planner-btn">
                        Otevřít Timeline
                    </button>
                </div>
            </div>
        `;
    }
}

// Styles
const plannerStyles = document.createElement('style');
plannerStyles.textContent = `
    .smart-planner {
        max-width: 600px;
        margin: 0 auto;
    }
    
    .planner-loading {
        text-align: center;
        padding: 40px;
        color: var(--text-secondary, #9ca8b3);
    }
    
    .planner-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .planner-greeting h2 {
        margin: 0;
        font-size: 24px;
    }
    
    .planner-greeting p {
        margin: 4px 0 0;
        color: var(--text-secondary, #9ca8b3);
    }
    
    .planner-score {
        text-align: center;
    }
    
    .score-circle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    
    .score-circle.good { background: rgba(74, 222, 128, 0.2); color: var(--mint, #4ade80); }
    .score-circle.medium { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
    .score-circle.bad { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
    
    .planner-score span {
        font-size: 11px;
        color: var(--text-secondary, #9ca8b3);
    }
    
    .planner-weather {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 12px;
        margin-bottom: 16px;
    }
    
    .weather-icon { font-size: 32px; }
    .weather-temp { font-size: 24px; font-weight: 700; }
    .weather-desc { color: var(--text-secondary, #9ca8b3); }
    
    .planner-warnings {
        margin-bottom: 16px;
    }
    
    .warning-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    .warning-item.high {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #fca5a5;
    }
    
    .warning-item.medium {
        background: rgba(251, 191, 36, 0.15);
        border: 1px solid rgba(251, 191, 36, 0.3);
        color: #fcd34d;
    }
    
    .warning-item.weather {
        background: rgba(96, 165, 250, 0.15);
        border: 1px solid rgba(96, 165, 250, 0.3);
        color: #93c5fd;
    }
    
    .planner-section {
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }
    
    .planner-section.urgent {
        border-color: rgba(239, 68, 68, 0.3);
        background: rgba(239, 68, 68, 0.05);
    }
    
    .planner-section h3 {
        margin: 0 0 12px;
        font-size: 16px;
    }
    
    .task-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .task-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 10px 12px;
        background: var(--bg-elevated, #242a33);
        border-radius: 8px;
    }
    
    .task-item.urgent {
        border-left: 3px solid #ef4444;
    }
    
    .task-title { flex: 1; }
    .task-deadline { font-size: 12px; color: var(--text-secondary, #9ca8b3); }
    
    .empty {
        color: var(--text-secondary, #9ca8b3);
        text-align: center;
        padding: 20px;
    }
    
    .more {
        color: var(--text-secondary, #9ca8b3);
        font-size: 13px;
        text-align: center;
        margin: 8px 0 0;
    }
    
    .team-recommendations {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .recommendation-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px;
        background: var(--bg-elevated, #242a33);
        border-radius: 8px;
    }
    
    .rec-arrow {
        color: var(--mint, #4ade80);
    }
    
    .suggestions-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    
    .suggestion-item {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px;
        background: var(--bg-elevated, #242a33);
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .suggestion-item:hover {
        background: rgba(74, 222, 128, 0.1);
    }
    
    .suggestion-icon { font-size: 18px; }
    .suggestion-arrow { margin-left: auto; color: var(--text-secondary, #9ca8b3); }
    
    .planner-actions {
        display: flex;
        gap: 12px;
        margin-top: 20px;
    }
    
    .planner-btn {
        flex: 1;
        padding: 14px;
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 10px;
        background: var(--bg-elevated, #242a33);
        color: var(--text-primary, #e8eef2);
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .planner-btn:hover {
        border-color: var(--mint, #4ade80);
    }
    
    .planner-btn.primary {
        background: var(--mint, #4ade80);
        color: #0a0e11;
        border-color: var(--mint, #4ade80);
    }
`;
document.head.appendChild(plannerStyles);

// Global instance
window.smartPlanner = new SmartPlanner();
