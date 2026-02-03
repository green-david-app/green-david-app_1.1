// Multi-Select Dropdown Component
class MultiSelectDropdown {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        
        if (!this.container) {
            console.error(`MultiSelectDropdown: Container #${containerId} not found!`);
            return;
        }
        
        this.employees = options.employees || [];
        this.selected = options.selected || [];
        this.primaryId = options.primaryId || null;
        this.placeholder = options.placeholder || 'Vybrat člena teamu';
        this.onChange = options.onChange || (() => {});
        
        this.isOpen = false;
        console.log(`MultiSelectDropdown created for #${containerId} with ${this.employees.length} employees`);
        this.render();
        this.attachEventListeners();
    }
    
    render() {
        if (!this.container) {
            console.warn(`Cannot render: container #${this.containerId} not found`);
            return;
        }
        
        const selectedEmployees = this.employees.filter(e => this.selected.includes(e.id));
        
        this.container.innerHTML = `
            <div class="multi-select-dropdown ${this.isOpen ? 'open' : ''}">
                <div class="multi-select-trigger">
                    <div class="multi-select-selected">
                        ${selectedEmployees.length === 0 ? 
                            `<span class="multi-select-placeholder">${this.placeholder}</span>` :
                            selectedEmployees.map(emp => this.renderChip(emp)).join('')
                        }
                    </div>
                    <span class="multi-select-arrow">▼</span>
                </div>
                <div class="multi-select-menu">
                    ${this.employees.map(emp => this.renderOption(emp)).join('')}
                </div>
            </div>
        `;
    }
    
    renderChip(employee) {
        const isPrimary = employee.id === this.primaryId;
        return `
            <span class="multi-select-chip ${isPrimary ? 'primary' : ''}">
                ${employee.name}
                ${isPrimary ? '★' : ''}
                <button onclick="window.multiSelectInstance_${this.container.id}.remove(${employee.id}); event.stopPropagation();">×</button>
            </span>
        `;
    }
    
    renderOption(employee) {
        const isSelected = this.selected.includes(employee.id);
        const isPrimary = employee.id === this.primaryId;
        
        return `
            <label class="multi-select-option">
                <input type="checkbox" 
                       value="${employee.id}" 
                       ${isSelected ? 'checked' : ''}
                       onchange="window.multiSelectInstance_${this.container.id}.toggle(${employee.id}, this.checked); event.stopPropagation();">
                <span class="multi-select-option-label">${employee.name}</span>
                ${isSelected ? `
                    <span class="multi-select-option-star ${isPrimary ? 'primary' : ''}" 
                          onclick="window.multiSelectInstance_${this.container.id}.setPrimary(${employee.id}); event.stopPropagation();">
                        ${isPrimary ? '★' : '☆'}
                    </span>
                ` : ''}
            </label>
        `;
    }
    
    attachEventListeners() {
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target) && this.isOpen) {
                this.close();
            }
        });
        
        // Toggle dropdown
        const trigger = this.container.querySelector('.multi-select-trigger');
        if (trigger) {
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggle();
            });
        }
    }
    
    toggle() {
        this.isOpen = !this.isOpen;
        this.render();
        this.attachEventListeners();
    }
    
    open() {
        this.isOpen = true;
        this.render();
        this.attachEventListeners();
    }
    
    close() {
        this.isOpen = false;
        this.render();
        this.attachEventListeners();
    }
    
    toggle(empId, checked) {
        if (checked) {
            if (!this.selected.includes(empId)) {
                this.selected.push(empId);
                // Pokud je první, nastav jako primárního
                if (this.selected.length === 1) {
                    this.primaryId = empId;
                }
            }
        } else {
            this.selected = this.selected.filter(id => id !== empId);
            // Pokud byl primární, nastav nového
            if (this.primaryId === empId) {
                this.primaryId = this.selected.length > 0 ? this.selected[0] : null;
            }
        }
        this.render();
        this.attachEventListeners();
        this.onChange({
            selected: this.selected,
            primary: this.primaryId
        });
    }
    
    setPrimary(empId) {
        if (this.selected.includes(empId)) {
            this.primaryId = empId;
            this.render();
            this.attachEventListeners();
            this.onChange({
                selected: this.selected,
                primary: this.primaryId
            });
        }
    }
    
    remove(empId) {
        this.toggle(empId, false);
    }
    
    getSelection() {
        return {
            selected: this.selected,
            primary: this.primaryId
        };
    }
    
    setEmployees(employees) {
        this.employees = employees;
        this.render();
        this.attachEventListeners();
    }
    
    reset() {
        this.selected = [];
        this.primaryId = null;
        this.render();
        this.attachEventListeners();
        this.onChange({
            selected: this.selected,
            primary: this.primaryId
        });
    }
}

window.MultiSelectDropdown = MultiSelectDropdown;
