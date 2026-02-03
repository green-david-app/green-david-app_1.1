/**
 * Widget Editor - Drag & Drop a správa widgetů
 */

const WidgetEditor = {
    currentWidgets: [],
    availableWidgets: [],
    mode: 'field',
    
    init() {
        this.loadWidgets();
        this.setupDragAndDrop();
    },
    
    loadWidgets() {
        // Načti aktuální widgety z DOM
        const activeList = document.getElementById('activeWidgetsList');
        if (activeList) {
            this.currentWidgets = Array.from(activeList.querySelectorAll('.widget-item'))
                .map(item => item.dataset.id);
        }
        
        // Načti dostupné widgety z DOM
        const availableList = document.getElementById('availableWidgetsList');
        if (availableList) {
            this.availableWidgets = Array.from(availableList.querySelectorAll('.widget-item'))
                .map(item => item.dataset.id);
        }
        
        // Získej mód z URL nebo z DOM
        const urlParams = new URLSearchParams(window.location.search);
        this.mode = urlParams.get('mode') || document.body.dataset.mode || 'field';
    },
    
    setupDragAndDrop() {
        const activeList = document.getElementById('activeWidgetsList');
        if (!activeList) return;
        
        // Drag start
        activeList.addEventListener('dragstart', (e) => {
            if (e.target.classList.contains('widget-item')) {
                e.target.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/html', e.target.outerHTML);
                e.dataTransfer.setData('widget-id', e.target.dataset.id);
            }
        });
        
        // Drag end
        activeList.addEventListener('dragend', (e) => {
            e.target.classList.remove('dragging');
        });
        
        // Drag over
        activeList.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
            
            const afterElement = this.getDragAfterElement(activeList, e.clientY);
            const dragging = activeList.querySelector('.dragging');
            
            if (afterElement == null) {
                activeList.appendChild(dragging);
            } else {
                activeList.insertBefore(dragging, afterElement);
            }
        });
        
        // Drop z available widgets
        const availableList = document.getElementById('availableWidgetsList');
        if (availableList) {
            availableList.addEventListener('dragstart', (e) => {
                if (e.target.classList.contains('widget-item')) {
                    e.dataTransfer.effectAllowed = 'copy';
                    e.dataTransfer.setData('widget-id', e.target.dataset.id);
                }
            });
            
            activeList.addEventListener('drop', (e) => {
                e.preventDefault();
                const widgetId = e.dataTransfer.getData('widget-id');
                if (widgetId && !this.currentWidgets.includes(widgetId)) {
                    this.addWidget(widgetId);
                }
            });
        }
    },
    
    getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('.widget-item:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    },
    
    addWidget(widgetId) {
        if (this.currentWidgets.includes(widgetId)) {
            return;
        }
        
        this.currentWidgets.push(widgetId);
        this.renderActiveWidgets();
        this.updateAvailableWidgets();
    },
    
    removeWidget(widgetId) {
        this.currentWidgets = this.currentWidgets.filter(id => id !== widgetId);
        this.renderActiveWidgets();
        this.updateAvailableWidgets();
    },
    
    renderActiveWidgets() {
        const list = document.getElementById('activeWidgetsList');
        if (!list) return;
        
        list.innerHTML = '';
        this.currentWidgets.forEach(widgetId => {
            const widget = window.widgetRegistry?.[widgetId];
            if (!widget) return;
            
            const item = document.createElement('div');
            item.className = 'widget-item';
            item.dataset.id = widgetId;
            item.draggable = true;
            item.innerHTML = `
                <span class="drag-handle">⋮⋮</span>
                <span class="widget-name">${widget.title}</span>
                <button class="btn-remove" onclick="WidgetEditor.removeWidget('${widgetId}')">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            `;
            list.appendChild(item);
        });
        
        this.setupDragAndDrop();
    },
    
    updateAvailableWidgets() {
        const list = document.getElementById('availableWidgetsList');
        if (!list) return;
        
        const available = this.availableWidgets.filter(id => !this.currentWidgets.includes(id));
        
        list.querySelectorAll('.widget-item').forEach(item => {
            const widgetId = item.dataset.id;
            if (this.currentWidgets.includes(widgetId)) {
                item.style.display = 'none';
            } else {
                item.style.display = '';
            }
        });
    },
    
    async saveLayout() {
        try {
            const response = await fetch('/api/user/dashboard-layout', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mode: this.mode,
                    widgets: this.currentWidgets
                })
            });
            
            if (response.ok) {
                alert('Layout uložen');
                window.location.href = `/mobile/dashboard?mode=${this.mode}`;
            } else {
                alert('Chyba při ukládání');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Chyba: ' + error.message);
        }
    },
    
    async resetToDefault() {
        if (!confirm('Obnovit výchozí layout? Všechny změny budou ztraceny.')) {
            return;
        }
        
        try {
            const response = await fetch('/api/user/dashboard-layout', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode: this.mode })
            });
            
            if (response.ok) {
                alert('Výchozí layout obnoven');
                location.reload();
            } else {
                alert('Chyba při obnovování');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Chyba: ' + error.message);
        }
    }
};

// Globální funkce pro onclick handlery
window.addWidget = function(widgetId) {
    WidgetEditor.addWidget(widgetId);
};

window.removeWidget = function(widgetId) {
    WidgetEditor.removeWidget(widgetId);
};

window.saveLayout = function() {
    WidgetEditor.saveLayout();
};

window.resetToDefault = function() {
    WidgetEditor.resetToDefault();
};

// Inicializace
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => WidgetEditor.init());
} else {
    WidgetEditor.init();
}
