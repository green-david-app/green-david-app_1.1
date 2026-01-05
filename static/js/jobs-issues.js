// Jobs Issues Integration
// Replaces old problems system with new Issues API

// Override addProblem to use API
window.addProblem = async function(jobId) {
    const titleEl = document.getElementById('ops-problem-title');
    const noteEl = document.getElementById('ops-problem-note');
    const sevEl = document.getElementById('ops-problem-severity');

    const title = (titleEl?.value || '').trim();
    const note = (noteEl?.value || '').trim();
    const severity = (sevEl?.value || 'blocking');
    
    // Get selected employees
    const assignedEmployees = window.issueSelectedEmployees || [];
    const primaryEmployee = assignedEmployees.length > 0 ? assignedEmployees[0] : null;

    if (!title) {
        if (window.showToast) window.showToast('Zadej název issue', 'error');
        return;
    }

    try {
        const res = await fetch('/api/issues', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                job_id: jobId,
                title: title,
                description: note,
                type: severity === 'info' ? 'note' : 'blocker',
                severity: severity,
                assigned_to: primaryEmployee,
                assigned_employees: assignedEmployees,
                primary_employee: primaryEmployee
            })
        });

        if (res.ok) {
            titleEl.value = '';
            noteEl.value = '';
            window.issueSelectedEmployees = [];
            if (window.renderOperativa) window.renderOperativa(jobId);
            if (window.showToast) window.showToast('Issue přidán', 'success');
        } else {
            throw new Error('Nepodařilo se přidat issue');
        }
    } catch (e) {
        console.error(e);
        if (window.showToast) window.showToast('Chyba při přidávání issue', 'error');
    }
};

// Override resolveProblem to use API
window.resolveProblem = async function(jobId, problemId) {
    try {
        const res = await fetch('/api/issues', {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                id: problemId,
                status: 'resolved'
            })
        });

        if (res.ok) {
            if (window.renderOperativa) window.renderOperativa(jobId);
            if (window.showToast) window.showToast('Issue vyřešen', 'success');
        }
    } catch (e) {
        console.error(e);
        if (window.showToast) window.showToast('Chyba při řešení issue', 'error');
    }
};

// Override deleteProblem to use API
window.deleteProblem = async function(jobId, problemId) {
    if (!confirm('Opravdu smazat tento issue?')) return;
    
    try {
        const res = await fetch(`/api/issues?id=${problemId}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            if (window.renderOperativa) window.renderOperativa(jobId);
            if (window.showToast) window.showToast('Issue smazán', 'success');
        }
    } catch (e) {
        console.error(e);
        if (window.showToast) window.showToast('Chyba při mazání issue', 'error');
    }
};

// Wrap renderOperativa to load issues from API
if (window.renderOperativa) {
    const originalRenderOperativa = window.renderOperativa;
    
    window.renderOperativa = async function(jobId) {
        // Load issues from API
        let issues = [];
        try {
            const res = await fetch(`/api/issues?job_id=${jobId}`);
            const data = await res.json();
            if (data.ok) {
                issues = data.issues || [];
            }
        } catch (e) {
            console.error('Error loading issues:', e);
        }

        // Transform API issues to old format for compatibility
        const ops = window.loadOps ? window.loadOps(jobId) : { problems: [], todos: [] };
        ops.problems = issues.map(i => ({
            id: i.id,
            title: i.title,
            note: i.description,
            severity: i.severity || i.type,
            ownerId: i.assigned_to,
            ownerName: i.assigned_name,
            status: i.status,
            createdAt: i.created_at
        }));

        // Call original render with modified ops
        // Temporarily override loadOps to return our data
        const originalLoadOps = window.loadOps;
        window.loadOps = function() { return ops; };
        
        originalRenderOperativa(jobId);
        
        window.loadOps = originalLoadOps;
    };
}

console.log('✓ Jobs Issues API integration loaded');
