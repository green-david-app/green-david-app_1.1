/**
 * Dashboard Widgets System
 * Drag & drop customizable widgets
 */

class DashboardWidgets {
    constructor() {
        this.widgets = [];
        this.layout = this.loadLayout();
        this.draggedWidget = null;
        this.editMode = false;
        
        // Available widget types
        this.widgetTypes = {
            'stats': { name: 'Statistiky', icon: '📊', minW: 1, minH: 1 },
            'weather': { name: 'Počasí', icon: '🌤️', minW: 1, minH: 1 },
            'urgent-tasks': { name: 'Urgentní úkoly', icon: '⚠️', minW: 2, minH: 1 },
            'quick-add': { name: 'Rychlé přidání', icon: '⚡', minW: 2, minH: 1 },
            'recent-jobs': { name: 'Poslední zakázky', icon: '📋', minW: 2, minH: 2 },
            'calendar': { name: 'Mini kalendář', icon: '📅', minW: 1, minH: 2 },
            'team-status': { name: 'Stav týmu', icon: '👥', minW: 1, minH: 1 },
            'deadlines': { name: 'Blížící se termíny', icon: '⏰', minW: 2, minH: 1 },
            'quick-actions': { name: 'Rychlé akce', icon: '🚀', minW: 2, minH: 2 },
            'notes': { name: 'Poznámky', icon: '📝', minW: 1, minH: 1 },
            'low-stock': { name: 'Nízké zásoby', icon: '📦', minW: 1, minH: 1 },
            'gantt-preview': { name: 'Timeline preview', icon: '📈', minW: 3, minH: 1 }
        };
    }

    loadLayout() {
        try {
            const saved = localStorage.getItem('dashboard-layout');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {
            console.error('Error loading layout:', e);
        }
        // Default layout
        return {
            widgets: [
                { id: 'stats', type: 'stats', x: 0, y: 0, w: 2, h: 1, visible: true },
                { id: 'weather', type: 'weather', x: 2, y: 0, w: 1, h: 1, visible: true },
                { id: 'quick-add', type: 'quick-add', x: 0, y: 1, w: 3, h: 1, visible: true },
                { id: 'urgent-tasks', type: 'urgent-tasks', x: 0, y: 2, w: 3, h: 1, visible: true },
                { id: 'quick-actions', type: 'quick-actions', x: 0, y: 3, w: 3, h: 2, visible: true },
                { id: 'deadlines', type: 'deadlines', x: 0, y: 5, w: 2, h: 1, visible: false },
                { id: 'gantt-preview', type: 'gantt-preview', x: 0, y: 6, w: 3, h: 1, visible: false }
            ]
        };
    }

    saveLayout() {
        try {
            localStorage.setItem('dashboard-layout', JSON.stringify(this.layout));
        } catch (e) {
            console.error('Error saving layout:', e);
        }
    }

    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Widget container not found:', containerId);
            return;
        }
        
        this.render();
        this.setupDragAndDrop();
    }

    render() {
        // Add edit button
        this.renderEditButton();
        
        // Create widget grid
        const grid = document.createElement('div');
        grid.className = 'widget-grid' + (this.editMode ? ' edit-mode' : '');
        grid.id = 'widget-grid';
        
        // Sort widgets by position
        const visibleWidgets = this.layout.widgets
            .filter(w => w.visible)
            .sort((a, b) => (a.y * 10 + a.x) - (b.y * 10 + b.x));
        
        visibleWidgets.forEach(widget => {
            const el = this.createWidgetElement(widget);
            grid.appendChild(el);
        });
        
        // Replace or append grid
        const existingGrid = document.getElementById('widget-grid');
        if (existingGrid) {
            existingGrid.replaceWith(grid);
        } else {
            this.container.appendChild(grid);
        }
        
        // Add widget picker if in edit mode
        if (this.editMode) {
            this.renderWidgetPicker();
        }
    }

    renderEditButton() {
        let btn = document.getElementById('widget-edit-btn');
        if (!btn) {
            btn = document.createElement('button');
            btn.id = 'widget-edit-btn';
            btn.className = 'widget-edit-btn';
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
                <span>${this.editMode ? 'Hotovo' : 'Upravit'}</span>
            `;
            btn.onclick = () => this.toggleEditMode();
            
            // Insert before grid
            const firstChild = this.container.firstChild;
            if (firstChild) {
                this.container.insertBefore(btn, firstChild);
            } else {
                this.container.appendChild(btn);
            }
        } else {
            btn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                    ${this.editMode 
                        ? '<polyline points="20 6 9 17 4 12"/>' 
                        : '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>'}
                </svg>
                <span>${this.editMode ? 'Hotovo' : 'Upravit'}</span>
            `;
        }
    }

    toggleEditMode() {
        this.editMode = !this.editMode;
        this.render();
        
        if (!this.editMode) {
            this.saveLayout();
            // Remove picker
            const picker = document.getElementById('widget-picker');
            if (picker) picker.remove();
        }
    }

    createWidgetElement(widget) {
        const el = document.createElement('div');
        el.className = 'dashboard-widget';
        el.dataset.widgetId = widget.id;
        el.dataset.widgetType = widget.type;
        el.style.gridColumn = `span ${widget.w}`;
        el.style.gridRow = `span ${widget.h}`;
        
        const typeInfo = this.widgetTypes[widget.type] || { name: widget.type, icon: '📦' };
        
        // Header with drag handle (only in edit mode)
        if (this.editMode) {
            el.innerHTML = `
                <div class="widget-header" draggable="true">
                    <span class="widget-icon">${typeInfo.icon}</span>
                    <span class="widget-title">${typeInfo.name}</span>
                    <button class="widget-remove" onclick="dashboardWidgets.removeWidget('${widget.id}')" title="Odebrat">×</button>
                </div>
                <div class="widget-content" id="widget-content-${widget.id}">
                    <div class="widget-placeholder">Widget obsah</div>
                </div>
            `;
            el.classList.add('editable');
        } else {
            el.innerHTML = `
                <div class="widget-content" id="widget-content-${widget.id}"></div>
            `;
        }
        
        return el;
    }

    renderWidgetPicker() {
        let picker = document.getElementById('widget-picker');
        if (!picker) {
            picker = document.createElement('div');
            picker.id = 'widget-picker';
            picker.className = 'widget-picker';
            this.container.appendChild(picker);
        }
        
        const hiddenWidgets = this.layout.widgets.filter(w => !w.visible);
        const availableTypes = Object.keys(this.widgetTypes).filter(type => 
            !this.layout.widgets.some(w => w.type === type && w.visible)
        );
        
        picker.innerHTML = `
            <h4>Přidat widget</h4>
            <div class="widget-picker-grid">
                ${availableTypes.map(type => {
                    const info = this.widgetTypes[type];
                    return `
                        <div class="widget-picker-item" onclick="dashboardWidgets.addWidget('${type}')">
                            <span class="picker-icon">${info.icon}</span>
                            <span class="picker-name">${info.name}</span>
                        </div>
                    `;
                }).join('')}
            </div>
        `;
    }

    addWidget(type) {
        // Check if widget of this type exists but is hidden
        const existing = this.layout.widgets.find(w => w.type === type && !w.visible);
        if (existing) {
            existing.visible = true;
        } else {
            // Create new widget
            const typeInfo = this.widgetTypes[type];
            this.layout.widgets.push({
                id: `${type}-${Date.now()}`,
                type: type,
                x: 0,
                y: 99,
                w: typeInfo.minW || 1,
                h: typeInfo.minH || 1,
                visible: true
            });
        }
        
        this.render();
    }

    removeWidget(id) {
        const widget = this.layout.widgets.find(w => w.id === id);
        if (widget) {
            widget.visible = false;
            this.render();
        }
    }

    setupDragAndDrop() {
        if (!this.editMode) return;
        
        const grid = document.getElementById('widget-grid');
        if (!grid) return;
        
        grid.querySelectorAll('.widget-header').forEach(header => {
            header.addEventListener('dragstart', (e) => {
                this.draggedWidget = header.parentElement;
                this.draggedWidget.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            });
            
            header.addEventListener('dragend', () => {
                if (this.draggedWidget) {
                    this.draggedWidget.classList.remove('dragging');
                    this.draggedWidget = null;
                }
                this.updateLayoutFromDOM();
            });
        });
        
        grid.querySelectorAll('.dashboard-widget').forEach(widget => {
            widget.addEventListener('dragover', (e) => {
                e.preventDefault();
                if (this.draggedWidget && this.draggedWidget !== widget) {
                    const rect = widget.getBoundingClientRect();
                    const midY = rect.top + rect.height / 2;
                    if (e.clientY < midY) {
                        widget.parentElement.insertBefore(this.draggedWidget, widget);
                    } else {
                        widget.parentElement.insertBefore(this.draggedWidget, widget.nextSibling);
                    }
                }
            });
        });
    }

    updateLayoutFromDOM() {
        const grid = document.getElementById('widget-grid');
        if (!grid) return;
        
        const widgets = grid.querySelectorAll('.dashboard-widget');
        widgets.forEach((el, index) => {
            const id = el.dataset.widgetId;
            const layoutWidget = this.layout.widgets.find(w => w.id === id);
            if (layoutWidget) {
                layoutWidget.y = index;
            }
        });
    }

    // Method to render actual widget content
    renderWidgetContent(widgetId, content) {
        const container = document.getElementById(`widget-content-${widgetId}`);
        if (container) {
            if (typeof content === 'string') {
                container.innerHTML = content;
            } else if (content instanceof HTMLElement) {
                container.innerHTML = '';
                container.appendChild(content);
            }
        }
    }

    resetLayout() {
        localStorage.removeItem('dashboard-layout');
        this.layout = this.loadLayout();
        this.render();
    }
}

// Inject CSS
const widgetStyles = document.createElement('style');
widgetStyles.textContent = `
    .widget-edit-btn {
        position: fixed;
        bottom: 100px;
        right: 20px;
        z-index: 1000;
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 20px;
        background: linear-gradient(135deg, #4ade80, #7bc47e);
        border: none;
        border-radius: 30px;
        color: #0a0e11;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(159, 212, 161, 0.4);
        transition: all 0.3s ease;
    }
    .widget-edit-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(159, 212, 161, 0.5);
    }
    
    .widget-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        margin-bottom: 24px;
    }
    
    .widget-grid.edit-mode {
        background: rgba(159, 212, 161, 0.05);
        border: 2px dashed rgba(159, 212, 161, 0.3);
        border-radius: 16px;
        padding: 20px;
        min-height: 200px;
    }
    
    .dashboard-widget {
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 16px;
        overflow: hidden;
        transition: all 0.3s ease;
    }
    
    .dashboard-widget.editable {
        border: 2px solid rgba(159, 212, 161, 0.3);
    }
    
    .dashboard-widget.editable:hover {
        border-color: var(--mint, #4ade80);
    }
    
    .dashboard-widget.dragging {
        opacity: 0.5;
        transform: scale(1.02);
    }
    
    .widget-header {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 12px 16px;
        background: rgba(159, 212, 161, 0.1);
        border-bottom: 1px solid var(--border-primary, #2d3748);
        cursor: grab;
    }
    
    .widget-header:active {
        cursor: grabbing;
    }
    
    .widget-icon {
        font-size: 18px;
    }
    
    .widget-title {
        flex: 1;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-primary, #e8eef2);
    }
    
    .widget-remove {
        width: 24px;
        height: 24px;
        border: none;
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        border-radius: 6px;
        font-size: 18px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }
    
    .widget-remove:hover {
        background: rgba(239, 68, 68, 0.4);
    }
    
    .widget-content {
        padding: 16px;
    }
    
    .widget-placeholder {
        color: #6b7580;
        font-size: 13px;
        text-align: center;
        padding: 20px;
    }
    
    .widget-picker {
        margin-top: 24px;
        padding: 20px;
        background: var(--bg-card, #1a1f26);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 16px;
    }
    
    .widget-picker h4 {
        margin: 0 0 16px 0;
        color: var(--text-primary, #e8eef2);
        font-size: 16px;
    }
    
    .widget-picker-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 12px;
    }
    
    .widget-picker-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        padding: 16px;
        background: var(--bg-elevated, #242a33);
        border: 1px solid var(--border-primary, #2d3748);
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .widget-picker-item:hover {
        border-color: var(--mint, #4ade80);
        background: rgba(159, 212, 161, 0.1);
        transform: translateY(-2px);
    }
    
    .picker-icon {
        font-size: 24px;
    }
    
    .picker-name {
        font-size: 12px;
        color: var(--text-secondary, #9ca8b3);
        text-align: center;
    }
    
    @media (max-width: 768px) {
        .widget-grid {
            grid-template-columns: 1fr;
        }
        
        .widget-edit-btn {
            bottom: 80px;
            right: 16px;
            padding: 10px 16px;
        }
    }
`;
document.head.appendChild(widgetStyles);

// Global instance
window.dashboardWidgets = new DashboardWidgets();
