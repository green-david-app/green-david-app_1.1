// ====== MOVEMENTS MODULE ======

async function loadMovements() {
  try {
    const resp = await fetch('/api/warehouse/movements?limit=100');
    const data = await resp.json();
    if (data.success) {
      movements = data.movements || [];
      renderMovements();
    }
  } catch (e) {
    console.error('Error loading movements:', e);
  }
}

function renderMovements() {
  const typeFilter = document.getElementById('filterMovementType')?.value || '';
  const jobFilter = document.getElementById('filterMovementJob')?.value || '';

  let filtered = movements.filter(m => {
    if (typeFilter && m.movement_type !== typeFilter) return false;
    if (jobFilter && m.job_id !== parseInt(jobFilter)) return false;
    return true;
  });

  const html = filtered.map(m => {
    const typeIcon = getMovementTypeIcon(m.movement_type);
    const typeLabel = getMovementTypeLabel(m.movement_type);
    const typeColor = getMovementTypeColor(m.movement_type);

    return `
      <div style="padding:12px;border:1px solid var(--border-primary);border-radius:8px;margin-bottom:8px;border-left:3px solid ${typeColor};">
        <div style="display:flex;justify-content:space-between;align-items:start;">
          <div style="flex:1;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span style="font-size:20px;">${typeIcon}</span>
              <strong style="font-size:14px;">${escapeHtml(m.item_name || 'Neznámá položka')}</strong>
              <span class="badge" style="background:${typeColor}">${typeLabel}</span>
            </div>
            <div style="font-size:12px;color:var(--text-secondary);">
              Množství: <strong style="color:${typeColor}">${m.qty > 0 ? '+' : ''}${m.qty} ${escapeHtml(m.item_unit || 'ks')}</strong>
              ${m.job_title ? ` • Zakázka: ${escapeHtml(m.job_title)}` : ''}
              ${m.from_location ? ` • Z: ${escapeHtml(m.from_location)}` : ''}
              ${m.to_location ? ` • Do: ${escapeHtml(m.to_location)}` : ''}
              ${m.batch_number ? ` • Šarže: ${escapeHtml(m.batch_number)}` : ''}
            </div>
            ${m.note ? `<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">💬 ${escapeHtml(m.note)}</div>` : ''}
            <div style="font-size:11px;color:var(--text-secondary);margin-top:4px;">
              ${new Date(m.created_at).toLocaleString('cs-CZ')}
              ${m.employee_name ? ` • ${escapeHtml(m.employee_name)}` : ''}
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('movementsList').innerHTML = html || '<p style="padding:20px;text-align:center;color:var(--text-secondary);">Žádné pohyby</p>';
}

function getMovementTypeIcon(type) {
  const icons = {
    'in': '📥',
    'out': '📤',
    'return': '↩️',
    'transfer': '🔄',
    'adjustment': '⚙️',
    'inventory': '✅'
  };
  return icons[type] || '📦';
}

function getMovementTypeLabel(type) {
  const labels = {
    'in': 'Příjem',
    'out': 'Výdej',
    'return': 'Vrácení',
    'transfer': 'Přesun',
    'adjustment': 'Korekce',
    'inventory': 'Inventura'
  };
  return labels[type] || type;
}

function getMovementTypeColor(type) {
  const colors = {
    'in': '#4ade80',
    'out': '#fb923c',
    'return': '#3b82f6',
    'transfer': '#a78bfa',
    'adjustment': '#f59e0b',
    'inventory': '#10b981'
  };
  return colors[type] || '#6b7280';
}

function openMovementModal(itemId, defaultType = 'out') {
  const item = items.find(i => i.id === itemId);
  if (!item) return;

  currentItemId = itemId;
  document.getElementById('modalTitle').textContent = `Pohyb: ${item.name}`;
  document.getElementById('modalBody').innerHTML = renderMovementForm(item, defaultType);
  document.getElementById('btnSaveItem').textContent = 'Provést';
  document.getElementById('btnSaveItem').onclick = saveMovement;
  document.getElementById('itemModal').classList.add('show');

  // Setup movement type selection
  setupMovementTypeSelection(defaultType);
}

function renderMovementForm(item, defaultType) {
  return `
    <div style="margin-bottom:16px;padding:12px;background:rgba(178,251,165,0.1);border-radius:8px;">
      <div style="font-size:13px;color:var(--text-secondary);">Aktuální stav</div>
      <div style="font-size:18px;font-weight:600;color:#B2FBA5;margin-top:4px;">
        ${item.qty.toFixed(2)} ${escapeHtml(item.unit)}
        ${item.location ? ` • 📍 ${escapeHtml(item.location)}` : ''}
      </div>
    </div>

    <div class="form-group">
      <label>Typ pohybu *</label>
      <div class="movement-type-select" id="movementTypeSelect">
        <div class="movement-type-btn ${defaultType === 'in' ? 'selected' : ''}" data-type="in" onclick="selectMovementType('in')">
          <div class="icon">📥</div>
          <div class="label">Příjem</div>
        </div>
        <div class="movement-type-btn ${defaultType === 'out' ? 'selected' : ''}" data-type="out" onclick="selectMovementType('out')">
          <div class="icon">📤</div>
          <div class="label">Výdej</div>
        </div>
        <div class="movement-type-btn ${defaultType === 'return' ? 'selected' : ''}" data-type="return" onclick="selectMovementType('return')">
          <div class="icon">↩️</div>
          <div class="label">Vrácení</div>
        </div>
        <div class="movement-type-btn ${defaultType === 'transfer' ? 'selected' : ''}" data-type="transfer" onclick="selectMovementType('transfer')">
          <div class="icon">🔄</div>
          <div class="label">Přesun</div>
        </div>
        <div class="movement-type-btn ${defaultType === 'adjustment' ? 'selected' : ''}" data-type="adjustment" onclick="selectMovementType('adjustment')">
          <div class="icon">⚙️</div>
          <div class="label">Korekce</div>
        </div>
      </div>
      <input type="hidden" id="movementType" value="${defaultType}">
    </div>

    <div class="form-group">
      <label>Množství *</label>
      <input type="number" step="0.01" id="movementQty" placeholder="0" required>
      <small style="color:var(--text-secondary);">Jednotka: ${escapeHtml(item.unit)}</small>
    </div>

    <div class="form-group" id="jobSelectGroup" style="display:${defaultType === 'out' || defaultType === 'return' ? 'block' : 'none'};">
      <label>Zakázka ${defaultType === 'out' ? '*' : '(volitelné)'}</label>
      <select id="movementJob" ${defaultType === 'out' ? 'required' : ''}>
        <option value="">-- Vyberte zakázku --</option>
      </select>
    </div>

    <div class="form-group" id="fromLocationGroup" style="display:${defaultType === 'transfer' ? 'block' : 'none'};">
      <label>Z lokace</label>
      <input type="text" id="movementFromLocation" value="${escapeHtml(item.location || '')}" readonly>
    </div>

    <div class="form-group" id="toLocationGroup" style="display:${defaultType === 'transfer' ? 'block' : 'none'};">
      <label>Do lokace *</label>
      <select id="movementToLocation">
        <option value="">-- Vyberte lokaci --</option>
      </select>
    </div>

    <div class="form-group">
      <label>Číslo šarže (volitelné)</label>
      <input type="text" id="movementBatch" value="${escapeHtml(item.batch_number || '')}" placeholder="LOT-2024-001">
    </div>

    <div class="form-group">
      <label>Poznámka</label>
      <textarea id="movementNote" rows="3" placeholder="Dodatečné informace..."></textarea>
    </div>

    <div id="movementWarning" style="display:none;padding:12px;background:rgba(251,146,60,0.1);border-radius:8px;margin-top:12px;">
      <p style="font-size:13px;margin:0;color:#fb923c;">⚠️ <span id="warningText"></span></p>
    </div>
  `;
}

function setupMovementTypeSelection(defaultType) {
  // Load jobs into select
  const jobSelect = document.getElementById('movementJob');
  if (jobSelect) {
    jobSelect.innerHTML = '<option value="">-- Vyberte zakázku --</option>';
    jobs.forEach(job => {
      const opt = document.createElement('option');
      opt.value = job.id;
      opt.textContent = `${job.code || ''} ${job.title || ''}`.trim();
      jobSelect.appendChild(opt);
    });
  }

  // Load locations into select
  const locationSelect = document.getElementById('movementToLocation');
  if (locationSelect) {
    locationSelect.innerHTML = '<option value="">-- Vyberte lokaci --</option>';
    locations.forEach(loc => {
      const opt = document.createElement('option');
      opt.value = loc.code;
      opt.textContent = loc.name;
      locationSelect.appendChild(opt);
    });
  }

  // Setup qty validation
  const qtyInput = document.getElementById('movementQty');
  if (qtyInput) {
    qtyInput.addEventListener('input', validateMovementQty);
  }
}

window.selectMovementType = function(type) {
  // Update UI
  document.querySelectorAll('.movement-type-btn').forEach(btn => {
    btn.classList.remove('selected');
  });
  document.querySelector(`.movement-type-btn[data-type="${type}"]`).classList.add('selected');
  document.getElementById('movementType').value = type;

  // Show/hide fields based on type
  const jobGroup = document.getElementById('jobSelectGroup');
  const fromLocationGroup = document.getElementById('fromLocationGroup');
  const toLocationGroup = document.getElementById('toLocationGroup');
  const jobSelect = document.getElementById('movementJob');

  if (type === 'out') {
    jobGroup.style.display = 'block';
    jobSelect.required = true;
    fromLocationGroup.style.display = 'none';
    toLocationGroup.style.display = 'none';
  } else if (type === 'return') {
    jobGroup.style.display = 'block';
    jobSelect.required = false;
    fromLocationGroup.style.display = 'none';
    toLocationGroup.style.display = 'none';
  } else if (type === 'transfer') {
    jobGroup.style.display = 'none';
    jobSelect.required = false;
    fromLocationGroup.style.display = 'block';
    toLocationGroup.style.display = 'block';
  } else {
    jobGroup.style.display = 'none';
    jobSelect.required = false;
    fromLocationGroup.style.display = 'none';
    toLocationGroup.style.display = 'none';
  }

  validateMovementQty();
};

function validateMovementQty() {
  const item = items.find(i => i.id === currentItemId);
  if (!item) return;

  const type = document.getElementById('movementType').value;
  const qty = parseFloat(document.getElementById('movementQty').value) || 0;
  const warning = document.getElementById('movementWarning');
  const warningText = document.getElementById('warningText');

  if (type === 'out' && qty > item.qty) {
    warning.style.display = 'block';
    warningText.textContent = `Nedostatečné množství na skladě. Dostupné: ${item.qty.toFixed(2)} ${item.unit}`;
  } else if (qty <= 0) {
    warning.style.display = 'block';
    warningText.textContent = 'Množství musí být větší než 0';
  } else {
    warning.style.display = 'none';
  }
}

async function saveMovement() {
  const type = document.getElementById('movementType').value;
  const qty = parseFloat(document.getElementById('movementQty').value);
  const jobId = document.getElementById('movementJob')?.value || null;
  const toLocation = document.getElementById('movementToLocation')?.value || '';
  const batch = document.getElementById('movementBatch')?.value.trim() || '';
  const note = document.getElementById('movementNote')?.value.trim() || '';

  if (!type || !qty || qty <= 0) {
    alert('Vyplňte všechna povinná pole');
    return;
  }

  if (type === 'out' && !jobId) {
    alert('Pro výdej je nutné vybrat zakázku');
    return;
  }

  if (type === 'transfer' && !toLocation) {
    alert('Pro přesun je nutné vybrat cílovou lokaci');
    return;
  }

  const item = items.find(i => i.id === currentItemId);
  if (type === 'out' && qty > item.qty) {
    if (!confirm(`Nedostatečné množství na skladě (${item.qty} ${item.unit}). Pokračovat s výdejem ${qty} ${item.unit}?`)) {
      return;
    }
  }

  try {
    const resp = await fetch('/api/warehouse/movements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        item_id: currentItemId,
        movement_type: type,
        qty: qty,
        job_id: jobId ? parseInt(jobId) : null,
        from_location: item.location || '',
        to_location: toLocation,
        batch_number: batch,
        note: note
      })
    });

    const data = await resp.json();
    if (data.success) {
      const typeLabel = getMovementTypeLabel(type);
      addHistory(`${typeLabel}: ${item.name} (${qty} ${item.unit})`);
      await loadItems();
      await loadStats();
      await loadMovements();
      window.closeModal();

      // Show success toast
      if (window.showToast) {
        window.showToast(`${typeLabel} proveden úspěšně`, 'success');
      }
    } else {
      alert(data.error || 'Chyba při vytváření pohybu');
    }
  } catch (e) {
    console.error('Error creating movement:', e);
    alert('Chyba při vytváření pohybu');
  }
}

// Event listeners for movements tab
document.getElementById('filterMovementType')?.addEventListener('change', renderMovements);
document.getElementById('filterMovementJob')?.addEventListener('change', renderMovements);

// Helper function for filtering movements by item
window.filterMovementsByItem = function(itemId) {
  // This would require adding item filter to the UI
  // For now, just load movements and highlight the item
  loadMovements();
};
