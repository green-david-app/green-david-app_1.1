// Task/Issue Detail Modal Functions

// Utility function to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Fetch JSON safely: avoids Safari "string did not match expected pattern" when backend returns HTML (e.g., 404/401)
async function fetchJsonSafe(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) {
        return { ok: false, status: res.status };
    }
    const ct = (res.headers.get('content-type') || '').toLowerCase();
    if (!ct.includes('application/json')) {
        return { ok: false, status: res.status };
    }
    try {
        return await res.json();
    } catch (e) {
        return { ok: false, status: res.status };
    }
}

let currentModalTask = null;
let currentModalJobId = null;
let currentModalType = null; // 'task' or 'issue'
let modalEmployees = [];
let modalComments = [];

async function openTaskDetail(jobId, taskId) {
    currentModalJobId = jobId;
    currentModalType = 'task';
    
    // Load task details from API
    try {
        const res = await fetch(`/api/tasks?id=${taskId}`);
        const data = await res.json();
        if (data.ok && data.task) {
            currentModalTask = data.task;
            showTaskDetailModal();
        }
    } catch (e) {
        console.error('Error loading task:', e);
        if (window.showToast) window.showToast('Chyba při načítání úkolu', 'error');
    }
}

async function openIssueDetail(jobId, issueId) {
    currentModalJobId = jobId;
    currentModalType = 'issue';
    
    // Load issue details from API
    try {
        const res = await fetch(`/api/issues?id=${issueId}`);
        const data = await res.json();
        if (data.ok && data.issue) {
            currentModalTask = data.issue;
            showTaskDetailModal();
        }
    } catch (e) {
        console.error('Error loading issue:', e);
        if (window.showToast) window.showToast('Chyba při načítání issue', 'error');
    }
}

function showTaskDetailModal() {
    const modal = document.getElementById('task-detail-modal');
    if (!modal || !currentModalTask) return;
    
    // Set title
    document.getElementById('modal-title').textContent = 
        currentModalType === 'task' ? 'Detail úkolu' : 'Detail issue';
    
    // Fill fields
    document.getElementById('modal-task-title').value = currentModalTask.title || '';
    document.getElementById('modal-task-description').value = currentModalTask.description || '';
    
    // Fill status
    const statusSelect = document.getElementById('modal-task-status');
    if (statusSelect) {
        statusSelect.value = currentModalTask.status || 'open';
    }
    
    // Fill employee dropdown
    const empSelect = document.getElementById('modal-add-employee');
    if (empSelect && employees) {
        empSelect.innerHTML = '<option value="">+ Přidat zaměstnance</option>';
        employees.forEach(emp => {
            const option = document.createElement('option');
            option.value = emp.id;
            option.textContent = emp.name;
            empSelect.appendChild(option);
        });
    }
    
    // Set modal employees from task
    modalEmployees = currentModalTask.assignees || [];
    renderModalEmployees();
    
    // Load comments
    loadComments();
    
    // Load attachments
    loadAttachments();
    
    // Load location
    loadLocation();
    
    // Show modal
    modal.classList.add('active');
}

function closeTaskDetailModal() {
    const modal = document.getElementById('task-detail-modal');
    if (modal) {
        modal.classList.remove('active');
    }
    currentModalTask = null;
    currentModalJobId = null;
    currentModalType = null;
    modalEmployees = [];
    modalComments = [];
}

function modalAddEmployee(empId) {
    if (!empId) return;
    empId = parseInt(empId);
    
    // Check if already added
    if (modalEmployees.some(e => e.id === empId)) return;
    
    const emp = employees.find(e => e.id === empId);
    if (!emp) return;
    
    modalEmployees.push({
        id: emp.id,
        name: emp.name,
        is_primary: modalEmployees.length === 0 // First one is primary
    });
    
    renderModalEmployees();
}

function modalRemoveEmployee(empId) {
    modalEmployees = modalEmployees.filter(e => e.id !== empId);
    
    // If removed was primary, make first one primary
    if (modalEmployees.length > 0 && !modalEmployees.some(e => e.is_primary)) {
        modalEmployees[0].is_primary = true;
    }
    
    renderModalEmployees();
}

function modalSetPrimaryEmployee(empId) {
    modalEmployees.forEach(e => {
        e.is_primary = e.id === empId;
    });
    renderModalEmployees();
}

function renderModalEmployees() {
    const container = document.getElementById('modal-employees-list');
    if (!container) return;
    
    if (modalEmployees.length === 0) {
        container.innerHTML = '<div style="opacity:0.5;font-size:13px;">Nikdo nepřiřazen</div>';
        return;
    }
    
    container.innerHTML = modalEmployees.map(emp => `
        <div class="task-detail-employee-item">
            <span class="task-detail-employee-name">${escapeHtml(emp.name)}</span>
            ${emp.is_primary ? 
                '<span class="task-detail-primary-badge">★ Hlavní</span>' :
                `<button class="btn-secondary" onclick="modalSetPrimaryEmployee(${emp.id})" style="padding:4px 8px;font-size:12px;">Nastavit hlavní</button>`
            }
            <button class="btn-secondary" onclick="modalRemoveEmployee(${emp.id})" style="padding:4px 8px;">×</button>
        </div>
    `).join('');
}

function addTaskComment() {
    const textarea = document.getElementById('modal-new-comment');
    if (!textarea) return;
    
    const text = textarea.value.trim();
    if (!text) return;
    
    modalComments.push({
        author: window.currentUser ? window.currentUser.name : 'Vy',
        text: text,
        timestamp: new Date().toISOString()
    });
    
    textarea.value = '';
    renderModalComments();
}

function renderModalComments() {
    const container = document.getElementById('modal-comments');
    if (!container) return;
    
    if (modalComments.length === 0) {
        container.innerHTML = '<div style="opacity:0.5;font-size:13px;">Zatím žádné poznámky</div>';
        return;
    }
    
    container.innerHTML = modalComments.map(comment => {
        const date = new Date(comment.timestamp);
        const timeStr = date.toLocaleString('cs-CZ', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        return `
            <div class="task-detail-comment">
                <div class="task-detail-comment-meta">
                    <span class="task-detail-comment-author">${escapeHtml(comment.author)}</span>
                    <span>${timeStr}</span>
                </div>
                <div class="task-detail-comment-text">${escapeHtml(comment.text)}</div>
            </div>
        `;
    }).join('');
}

async function saveTaskDetails() {
    if (!currentModalTask) return;
    
    const title = document.getElementById('modal-task-title').value.trim();
    const description = document.getElementById('modal-task-description').value.trim();
    const status = document.getElementById('modal-task-status')?.value || 'open';
    
    if (!title) {
        if (window.showToast) window.showToast('Zadej název', 'error');
        return;
    }
    
    const assignedIds = modalEmployees.map(e => e.id);
    const primaryId = modalEmployees.find(e => e.is_primary)?.id || null;
    
    try {
        const endpoint = currentModalType === 'task' ? '/api/tasks' : '/api/issues';
        const res = await fetch(endpoint, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                id: currentModalTask.id,
                title: title,
                description: description,
                status: status,
                assigned_employees: assignedIds,
                primary_employee: primaryId,
                employee_id: primaryId, // For tasks
                assigned_to: primaryId  // For issues
            })
        });
        
        if (res.ok) {
            if (window.showToast) window.showToast('Změny uloženy', 'success');
            closeTaskDetailModal();
            if (window.renderOperativa) window.renderOperativa(currentModalJobId);
            if (window.loadTasks) window.loadTasks();
            if (window.fetchIssues) window.fetchIssues();
        } else {
            throw new Error('Failed to save');
        }
    } catch (e) {
        console.error('Error saving:', e);
        if (window.showToast) window.showToast('Chyba při ukládání', 'error');
    }
}

async function deleteTaskFromModal() {
    if (!currentModalTask) return;
    
    if (!confirm(`Opravdu smazat tento ${currentModalType === 'task' ? 'úkol' : 'issue'}?`)) return;
    
    try {
        const endpoint = currentModalType === 'task' ? '/api/tasks' : '/api/issues';
        const res = await fetch(`${endpoint}?id=${currentModalTask.id}`, {
            method: 'DELETE'
        });
        
        if (res.ok) {
            if (window.showToast) window.showToast('Smazáno', 'success');
            closeTaskDetailModal();
            if (window.renderOperativa) window.renderOperativa(currentModalJobId);
        } else {
            throw new Error('Failed to delete');
        }
    } catch (e) {
        console.error('Error deleting:', e);
        if (window.showToast) window.showToast('Chyba při mazání', 'error');
    }
}

// Close modal on ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeTaskDetailModal();
    }
});

// Close modal on click outside
document.getElementById('task-detail-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'task-detail-modal') {
        closeTaskDetailModal();
    }
});

// === COMMENTS ===
async function loadComments() {
    if (!currentModalTask) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    try {
        const data = await fetchJsonSafe(`/api/${endpoint}/${currentModalTask.id}/comments`);
        if (data.ok) {
            modalComments = data.comments || [];
            renderModalComments();
        }
    } catch (e) {
        console.error('Error loading comments:', e);
    }
}

async function addTaskComment() {
    const textarea = document.getElementById('modal-new-comment');
    if (!textarea || !currentModalTask) return;
    
    const text = textarea.value.trim();
    if (!text) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    try {
        const res = await fetch(`/api/${endpoint}/${currentModalTask.id}/comments`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ comment: text })
        });
        
        if (res.ok) {
            textarea.value = '';
            loadComments();
        }
    } catch (e) {
        console.error('Error adding comment:', e);
    }
}

// === ATTACHMENTS ===
async function loadAttachments() {
    if (!currentModalTask) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    try {
        const data = await fetchJsonSafe(`/api/${endpoint}/${currentModalTask.id}/attachments`);
        if (data.ok) {
            renderAttachments(data.attachments || []);
        }
    } catch (e) {
        console.error('Error loading attachments:', e);
    }
}

function renderAttachments(attachments) {
    const container = document.getElementById('modal-files');
    if (!container) return;
    
    if (attachments.length === 0) {
        container.innerHTML = '<div style="opacity:0.5;font-size:13px;">Žádné přílohy</div>';
        return;
    }
    
    container.innerHTML = attachments.map(file => {
        const sizeKB = Math.round(file.file_size / 1024);
        return `
            <div class="task-detail-file">
                <span class="task-detail-file-name">📎 ${escapeHtml(file.original_filename)}</span>
                <span class="task-detail-file-size">${sizeKB} KB</span>
                <a href="/api/attachments/${file.filename}" target="_blank" class="btn-secondary" style="padding:4px 8px;font-size:12px;">Stáhnout</a>
                <button class="btn-secondary" onclick="deleteAttachment(${file.id})" style="padding:4px 8px;font-size:12px;">×</button>
            </div>
        `;
    }).join('');
}

async function handleFileSelect(files) {
    if (!files || files.length === 0 || !currentModalTask) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    
    for (let file of files) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch(`/api/${endpoint}/${currentModalTask.id}/attachments`, {
                method: 'POST',
                body: formData
            });
            
            if (!res.ok) {
                console.error('Upload failed for:', file.name);
            }
        } catch (e) {
            console.error('Error uploading file:', e);
        }
    }
    
    // Reload attachments
    loadAttachments();
}

function handleFileDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    e.target.style.borderColor = '#333';
    
    const files = e.dataTransfer.files;
    handleFileSelect(files);
}

async function deleteAttachment(fileId) {
    if (!confirm('Opravdu smazat přílohu?') || !currentModalTask) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    try {
        const res = await fetch(`/api/${endpoint}/${currentModalTask.id}/attachments?id=${fileId}`, {
            method: 'DELETE'
        });
        
        if (res.ok) {
            loadAttachments();
        }
    } catch (e) {
        console.error('Error deleting attachment:', e);
    }
}

// === GPS LOCATION ===
let currentMap = null;
let currentMarker = null;

async function loadLocation() {
    if (!currentModalTask) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    try {
        const data = await fetchJsonSafe(`/api/${endpoint}/${currentModalTask.id}/location`);
        if (data.ok && data.location) {
            showLocation(data.location);
        } else {
            hideLocation();
        }
    } catch (e) {
        console.error('Error loading location:', e);
        hideLocation();
    }
}

function showLocation(location) {
    document.getElementById('modal-location-display').style.display = 'block';
    document.getElementById('modal-location-actions').style.display = 'none';
    
    const coords = document.getElementById('modal-coords');
    const link = document.getElementById('modal-gmaps-link');
    
    coords.textContent = `${location.latitude.toFixed(6)}, ${location.longitude.toFixed(6)}`;
    link.href = `https://www.google.com/maps?q=${location.latitude},${location.longitude}`;
    
    // Initialize map
    initMap(location.latitude, location.longitude);
}

function hideLocation() {
    document.getElementById('modal-location-display').style.display = 'none';
    document.getElementById('modal-location-actions').style.display = 'flex';
}

function initMap(lat, lng) {
    const mapDiv = document.getElementById('modal-map');
    if (!mapDiv) return;
    
    // Simple map using Google Maps Static API
    mapDiv.innerHTML = `<img src="https://maps.googleapis.com/maps/api/staticmap?center=${lat},${lng}&zoom=15&size=600x200&markers=color:green%7C${lat},${lng}&key=YOUR_API_KEY" style="width:100%;height:100%;object-fit:cover;border-radius:6px;" alt="Mapa">`;
}

async function getCurrentLocation() {
    if (!navigator.geolocation) {
        alert('GPS není podporováno ve vašem prohlížeči');
        return;
    }
    
    navigator.geolocation.getCurrentPosition(async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        await saveLocation(lat, lng);
    }, (error) => {
        alert('Nepodařilo se získat polohu: ' + error.message);
    });
}

async function selectLocationOnMap() {
    // Pro jednoduchost použijeme prompt - můžeš později nahradit interaktivní mapou
    const input = prompt('Zadej souřadnice (formát: 50.0755, 14.4378):');
    if (!input) return;
    
    const parts = input.split(',').map(s => s.trim());
    if (parts.length !== 2) {
        alert('Neplatný formát');
        return;
    }
    
    const lat = parseFloat(parts[0]);
    const lng = parseFloat(parts[1]);
    
    if (isNaN(lat) || isNaN(lng)) {
        alert('Neplatné souřadnice');
        return;
    }
    
    await saveLocation(lat, lng);
}

async function saveLocation(lat, lng) {
    if (!currentModalTask) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    try {
        const res = await fetch(`/api/${endpoint}/${currentModalTask.id}/location`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ latitude: lat, longitude: lng })
        });
        
        if (res.ok) {
            loadLocation();
        }
    } catch (e) {
        console.error('Error saving location:', e);
    }
}

async function removeLocation() {
    if (!confirm('Opravdu smazat polohu?') || !currentModalTask) return;
    
    const endpoint = currentModalType === 'task' ? 'tasks' : 'issues';
    try {
        const res = await fetch(`/api/${endpoint}/${currentModalTask.id}/location`, {
            method: 'DELETE'
        });
        
        if (res.ok) {
            hideLocation();
        }
    } catch (e) {
        console.error('Error removing location:', e);
    }
}

