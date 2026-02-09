// Bulk Actions Module - Reusable bulk selection and actions
// Usage: BulkActions.init({ container, itemSelector, endpoint, actions })

(function() {
  'use strict';

  class BulkActionsManager {
    constructor(options = {}) {
      this.container = options.container || document.body;
      this.itemSelector = options.itemSelector || '.bulk-item';
      this.endpoint = options.endpoint || '/api/items';
      this.entityName = options.entityName || 'položek';
      this.selected = new Set();
      this.items = [];
      this.onSelectionChange = options.onSelectionChange || (() => {});
      
      this.actions = options.actions || [
        { id: 'delete', label: '🗑 Smazat', class: 'danger', confirm: true }
      ];
      
      this.init();
    }

    init() {
      this.createBulkBar();
      this.attachEventListeners();
    }

    createBulkBar() {
      // Check if bar already exists
      if (document.getElementById('bulk-actions-bar')) return;
      
      const bar = document.createElement('div');
      bar.id = 'bulk-actions-bar';
      bar.className = 'bulk-actions-bar';
      bar.innerHTML = `
        <span class="bulk-count"><span id="bulk-selected-count">0</span> ${this.entityName} vybráno</span>
        <div class="bulk-buttons">
          ${this.actions.map(a => `
            <button class="bulk-btn ${a.class || ''}" data-action="${a.id}">${a.label}</button>
          `).join('')}
          <button class="bulk-btn" data-action="cancel">✕ Zrušit</button>
        </div>
      `;
      
      document.body.appendChild(bar);
      
      // Add styles if not present
      if (!document.getElementById('bulk-actions-styles')) {
        const style = document.createElement('style');
        style.id = 'bulk-actions-styles';
        style.textContent = `
          .bulk-actions-bar {
            display: none;
            position: fixed;
            bottom: 100px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #1a1f24, #151a1e);
            border: 1px solid var(--mint, #4ade80);
            border-radius: 16px;
            padding: 12px 24px;
            gap: 16px;
            align-items: center;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            z-index: 10000;
          }
          .bulk-actions-bar.active { display: flex; }
          .bulk-count {
            background: var(--mint, #4ade80);
            color: #0a0e11;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
          }
          .bulk-buttons { display: flex; gap: 8px; }
          .bulk-btn {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #e8eef2;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
          }
          .bulk-btn:hover { background: rgba(255,255,255,0.2); }
          .bulk-btn.danger { border-color: #ef4444; color: #ef4444; }
          .bulk-btn.danger:hover { background: rgba(239,68,68,0.2); }
          .bulk-btn.success { border-color: var(--mint, #4ade80); color: var(--mint, #4ade80); }
          .bulk-btn.success:hover { background: rgba(74,222,128,0.2); }
          .bulk-btn.warning { border-color: #f59e0b; color: #f59e0b; }
          .bulk-btn.warning:hover { background: rgba(245,158,11,0.2); }
          
          /* Checkbox on items */
          .bulk-checkbox {
            position: absolute;
            top: 12px;
            left: 12px;
            width: 22px;
            height: 22px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 4px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            background: rgba(0,0,0,0.3);
            z-index: 10;
          }
          .bulk-checkbox:hover { border-color: var(--mint, #4ade80); }
          .bulk-item.selected .bulk-checkbox {
            background: var(--mint, #4ade80);
            border-color: var(--mint, #4ade80);
          }
          .bulk-item.selected .bulk-checkbox::after {
            content: "✓";
            color: #0a0e11;
            font-weight: bold;
            font-size: 14px;
          }
          .bulk-item.selected {
            border-color: var(--mint, #4ade80) !important;
            box-shadow: 0 0 0 2px rgba(74,222,128,0.3);
          }
          
          @media (max-width: 768px) {
            .bulk-actions-bar {
              flex-wrap: wrap;
              padding: 12px;
              bottom: 80px;
              width: calc(100% - 32px);
              justify-content: center;
            }
            .bulk-buttons { flex-wrap: wrap; justify-content: center; }
          }
        `;
        document.head.appendChild(style);
      }
      
      // Attach action handlers
      bar.querySelectorAll('.bulk-btn').forEach(btn => {
        btn.addEventListener('click', () => this.handleAction(btn.dataset.action));
      });
    }

    attachEventListeners() {
      // Select all button
      document.addEventListener('click', (e) => {
        if (e.target.matches('#btn-select-all, .btn-select-all')) {
          this.selectAll();
        }
      });
      
      // Keyboard shortcuts
      document.addEventListener('keydown', (e) => {
        // Escape to clear selection
        if (e.key === 'Escape' && this.selected.size > 0) {
          this.clearSelection();
        }
        // Ctrl+A to select all (when not in input)
        if (e.ctrlKey && e.key === 'a' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
          e.preventDefault();
          this.selectAll();
        }
      });
    }

    // Add checkbox to an item
    addCheckbox(item, itemId) {
      if (item.querySelector('.bulk-checkbox')) return;
      
      item.classList.add('bulk-item');
      item.dataset.bulkId = itemId;
      item.style.position = 'relative';
      
      const checkbox = document.createElement('div');
      checkbox.className = 'bulk-checkbox';
      checkbox.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleSelect(itemId);
      });
      
      item.insertBefore(checkbox, item.firstChild);
      
      // Update selected state
      if (this.selected.has(itemId)) {
        item.classList.add('selected');
      }
    }

    toggleSelect(itemId) {
      if (this.selected.has(itemId)) {
        this.selected.delete(itemId);
      } else {
        this.selected.add(itemId);
      }
      this.updateUI();
    }

    selectAll() {
      const items = document.querySelectorAll(this.itemSelector);
      if (this.selected.size === items.length) {
        this.clearSelection();
      } else {
        items.forEach(item => {
          const id = parseInt(item.dataset.bulkId || item.dataset.id || item.dataset.jobId);
          if (id) this.selected.add(id);
        });
        this.updateUI();
      }
    }

    clearSelection() {
      this.selected.clear();
      this.updateUI();
    }

    updateUI() {
      // Update bar
      const bar = document.getElementById('bulk-actions-bar');
      const count = document.getElementById('bulk-selected-count');
      
      if (this.selected.size > 0) {
        bar.classList.add('active');
        count.textContent = this.selected.size;
      } else {
        bar.classList.remove('active');
      }
      
      // Update item visual state
      document.querySelectorAll(this.itemSelector).forEach(item => {
        const id = parseInt(item.dataset.bulkId || item.dataset.id || item.dataset.jobId);
        if (this.selected.has(id)) {
          item.classList.add('selected');
        } else {
          item.classList.remove('selected');
        }
      });
      
      this.onSelectionChange(this.selected);
    }

    async handleAction(actionId) {
      if (actionId === 'cancel') {
        this.clearSelection();
        return;
      }
      
      const action = this.actions.find(a => a.id === actionId);
      if (!action) return;
      
      // Confirm if needed
      if (action.confirm) {
        if (!confirm(`Opravdu provést "${action.label}" pro ${this.selected.size} ${this.entityName}?`)) {
          return;
        }
      }
      
      // Custom handler
      if (action.handler) {
        await action.handler(Array.from(this.selected));
        this.clearSelection();
        return;
      }
      
      // Default: PATCH status or DELETE
      let success = 0;
      const ids = Array.from(this.selected);
      
      for (const id of ids) {
        try {
          let res;
          if (action.id === 'delete') {
            res = await fetch(`${this.endpoint}?id=${id}`, { method: 'DELETE' });
          } else if (action.status) {
            res = await fetch(this.endpoint, {
              method: 'PATCH',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ id: id, status: action.status })
            });
          }
          if (res && res.ok) success++;
        } catch (e) {
          console.error('Bulk action error:', e);
        }
      }
      
      // Show result
      if (window.showToast) {
        showToast(`${success} ${this.entityName} aktualizováno`, 'success');
      }
      
      this.clearSelection();
      
      // Reload if callback provided
      if (action.onComplete) {
        action.onComplete();
      }
    }

    getSelected() {
      return Array.from(this.selected);
    }

    setItems(items) {
      this.items = items;
    }
  }

  // Export globally
  window.BulkActions = BulkActionsManager;
})();
