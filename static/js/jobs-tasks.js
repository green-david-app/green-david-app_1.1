// Jobs Tasks Integration
// Replaces old todos system with Tasks API

// Override addTodo to use API
window.addTodo = async function(jobId) {
    const titleEl = document.getElementById('ops-todo-title');

    const title = (titleEl?.value || '').trim();
    
    // Get selected employees
    const assignedEmployees = window.taskSelectedEmployees || [];
    const primaryEmployee = assignedEmployees.length > 0 ? assignedEmployees[0] : null;

    if (!title) {
        if (window.showToast) window.showToast('Zadej název úkolu', 'error');
        return;
    }

    try {
        const res = await fetch('/api/tasks', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                job_id: jobId,
                title: title,
                status: 'open',
                employee_id: primaryEmployee,
                assigned_employees: assignedEmployees,
                primary_employee: primaryEmployee
            })
        });

        if (res.ok) {
            titleEl.value = '';
            window.taskSelectedEmployees = [];
            if (window.renderOperativa) window.renderOperativa(jobId);
            if (window.showToast) window.showToast('Úkol přidán', 'success');
        } else {
            throw new Error('Nepodařilo se přidat úkol');
        }
    } catch (e) {
        console.error(e);
        if (window.showToast) window.showToast('Chyba při přidávání úkolu', 'error');
    }
};

// Override completeTodo to use API
window.completeTodo = async function(jobId, todoId) {
    try {
        const res = await fetch('/api/tasks', {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                id: todoId,
                status: 'done'
            })
        });

        if (res.ok) {
            if (window.renderOperativa) window.renderOperativa(jobId);
            if (window.showToast) window.showToast('Úkol dokončen', 'success');
        }
    } catch (e) {
        console.error(e);
        if (window.showToast) window.showToast('Chyba při dokončování úkolu', 'error');
    }
};

// Override deleteTodo to use API
window.deleteTodo = async function(jobId, todoId) {
    if (!confirm('Opravdu smazat tento úkol?')) return;
    
    try {
        const res = await fetch(`/api/tasks?id=${todoId}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            if (window.renderOperativa) window.renderOperativa(jobId);
            if (window.showToast) window.showToast('Úkol smazán', 'success');
        }
    } catch (e) {
        console.error(e);
        if (window.showToast) window.showToast('Chyba při mazání úkolu', 'error');
    }
};

// Extend renderOperativa to load tasks from API
if (typeof window._originalRenderOperativa === 'undefined' && window.renderOperativa) {
    window._originalRenderOperativa = window.renderOperativa;
    
    window.renderOperativa = async function(jobId) {
        // Load tasks from API
        let tasks = [];
        try {
            const res = await fetch(`/api/tasks?job_id=${jobId}`);
            const data = await res.json();
            if (data.ok) {
                tasks = data.tasks || [];
            }
        } catch (e) {
            console.error('Error loading tasks:', e);
        }

        // Transform API tasks to old format for compatibility
        const ops = window.loadOps ? window.loadOps(jobId) : { problems: [], todos: [] };
        
        ops.todos = tasks.map(t => ({
            id: t.id,
            title: t.title,
            assigneeId: t.employee_id,
            assigneeName: t.employee_name,
            status: t.status === 'done' ? 'done' : 'open',
            createdAt: t.created_at,
            assignees: t.assignees || []  // Multi-assign support
        }));

        // Temporarily override loadOps to return our data
        const originalLoadOps = window.loadOps;
        window.loadOps = function() { return ops; };
        
        window._originalRenderOperativa(jobId);
        
        window.loadOps = originalLoadOps;
    };
}

console.log('✓ Jobs Tasks API integration loaded');
