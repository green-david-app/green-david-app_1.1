// employees.js - Complete logic for employees page

async function api(path, opts = {}) {
    const res = await fetch(path, {
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        ...opts
    });
    if (!res.ok) {
        let msg = res.statusText;
        try {
            const j = await res.json();
            msg = j.error || msg;
        } catch {}
        throw new Error(msg);
    }
    return await res.json();
}

let allEmployees = [];

// Load employees
async function loadEmployees() {
    const container = document.getElementById('employees-list');
    try {
        const data = await api('/api/employees');
        allEmployees = data.employees || [];
        renderEmployees();
    } catch (error) {
        console.error('Error loading employees:', error);
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">⚠️</div>
                <div class="empty-title">Chyba při načítání</div>
                <div class="empty-text">${error.message}</div>
            </div>
        `;
    }
}

// Render employees
function renderEmployees() {
    const container = document.getElementById('employees-list');
    
    if (allEmployees.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">👥</div>
                <div class="empty-title">Žádní zaměstnanci</div>
                <div class="empty-text">Přidejte prvního zaměstnance</div>
            </div>
        `;
        return;
    }
    
    const html = allEmployees.map(emp => {
        const roleClass = emp.role === 'admin' ? 'badge-warning' : 'badge-plan';
        const statusClass = emp.active ? 'badge-active' : 'badge-danger';
        
        return `
            <div class="card list-card" onclick="viewEmployee(${emp.id})">
                <div class="card-icon">
                    <svg viewBox="0 0 24 24">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                    </svg>
                </div>
                <div class="card-content">
                    <div class="card-title">${emp.name}</div>
                    <div class="card-subtitle">
                        <span class="card-badge ${roleClass}" style="display:inline-block;margin-right:8px;">${emp.role}</span>
                        <span class="card-badge ${statusClass}" style="display:inline-block;">${emp.active ? 'Aktivní' : 'Neaktivní'}</span>
                    </div>
                </div>
                <div style="color: var(--text-muted);">
                    <svg viewBox="0 0 24 24" style="width:20px;height:20px;">
                        <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// View employee detail
function viewEmployee(id) {
    // TODO: Show employee detail modal
    location.href = `/employees/${id}`;
}

// Show add employee modal
function showAddEmployee() {
    // TODO: Implement modal
    alert('Přidání zaměstnance - TODO: Modal');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadEmployees();
});
