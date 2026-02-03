// Multi-Employee Selector Component
// Umožňuje vybrat více členů teamu a označit primárního

class MultiEmployeeSelector {
    constructor(containerId, employees, options = {}) {
        this.container = document.getElementById(containerId);
        this.employees = employees || [];
        this.selectedIds = options.selectedIds || [];
        this.primaryId = options.primaryId || null;
        this.onChange = options.onChange || (() => {});
        
        this.render();
    }
    
    render() {
        if (!this.container) return;
        
        const selectedEmployees = this.employees.filter(e => this.selectedIds.includes(e.id));
        const availableEmployees = this.employees.filter(e => !this.selectedIds.includes(e.id));
        
        this.container.innerHTML = `
            <div style="background: #1a1a1a; border-radius: 8px; padding: 12px;">
                <!-- Selected employees -->
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 13px; opacity: 0.7; margin-bottom: 8px;">
                        Přiřazeno (${this.selectedIds.length})
                    </div>
                    <div id="selected-employees" style="display: flex; flex-wrap: wrap; gap: 6px; min-height: 32px;">
                        ${selectedEmployees.length === 0 ? 
                            '<div style="opacity: 0.5; font-size: 13px;">Nikdo nepřiřazen</div>' :
                            selectedEmployees.map(emp => this.renderEmployeeChip(emp)).join('')
                        }
                    </div>
                </div>
                
                <!-- Add employee dropdown -->
                <div>
                    <select id="add-employee-select" style="width: 100%; padding: 8px; border-radius: 6px; border: 1px solid #333; background: #0d0d0d; color: #fff;">
                        <option value="">+ Přidat člena teamu</option>
                        ${availableEmployees.map(emp => 
                            `<option value="${emp.id}">${emp.name}</option>`
                        ).join('')}
                    </select>
                </div>
            </div>
        `;
        
        // Event listener for adding employee
        const select = this.container.querySelector('#add-employee-select');
        if (select) {
            select.addEventListener('change', (e) => {
                const empId = parseInt(e.target.value);
                if (empId) {
                    this.addEmployee(empId);
                }
                e.target.value = '';
            });
        }
    }
    
    renderEmployeeChip(employee) {
        const isPrimary = employee.id === this.primaryId;
        
        return `
            <div style="background: ${isPrimary ? '#B2FBA5' : '#333'}; 
                        color: ${isPrimary ? '#000' : '#fff'}; 
                        padding: 6px 10px; 
                        border-radius: 16px; 
                        display: inline-flex; 
                        align-items: center; 
                        gap: 6px;
                        font-size: 13px;">
                <span>${employee.name}</span>
                ${isPrimary ? 
                    '<span style="font-weight: 700;">★</span>' : 
                    `<button onclick="window.multiSelector.setPrimary(${employee.id})" 
                             style="background: none; border: none; color: inherit; cursor: pointer; padding: 0; font-size: 12px;"
                             title="Nastavit jako hlavního">
                        ☆
                    </button>`
                }
                <button onclick="window.multiSelector.removeEmployee(${employee.id})" 
                        style="background: none; border: none; color: inherit; cursor: pointer; padding: 0; font-weight: 700;">
                    ×
                </button>
            </div>
        `;
    }
    
    addEmployee(empId) {
        if (!this.selectedIds.includes(empId)) {
            this.selectedIds.push(empId);
            
            // Pokud je první, nastav jako primárního
            if (this.selectedIds.length === 1) {
                this.primaryId = empId;
            }
            
            this.render();
            this.onChange({
                selectedIds: this.selectedIds,
                primaryId: this.primaryId
            });
        }
    }
    
    removeEmployee(empId) {
        this.selectedIds = this.selectedIds.filter(id => id !== empId);
        
        // Pokud byl primární, nastav nového
        if (this.primaryId === empId) {
            this.primaryId = this.selectedIds.length > 0 ? this.selectedIds[0] : null;
        }
        
        this.render();
        this.onChange({
            selectedIds: this.selectedIds,
            primaryId: this.primaryId
        });
    }
    
    setPrimary(empId) {
        if (this.selectedIds.includes(empId)) {
            this.primaryId = empId;
            this.render();
            this.onChange({
                selectedIds: this.selectedIds,
                primaryId: this.primaryId
            });
        }
    }
    
    getSelection() {
        return {
            selectedIds: this.selectedIds,
            primaryId: this.primaryId
        };
    }
}

// Global reference for button onclick handlers
window.multiSelector = null;

window.MultiEmployeeSelector = MultiEmployeeSelector;
