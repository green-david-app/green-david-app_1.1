// ====== LOCATIONS MODULE ======

async function loadLocations() {
  try {
    const resp = await fetch('/api/warehouse/locations');
    const data = await resp.json();
    if (data.success) {
      locations = data.locations || [];
      renderLocations();
    }
  } catch (e) {
    console.error('Error loading locations:', e);
  }
}

function renderLocations() {
  const html = locations.map(loc => `
    <div style="padding:16px;border:1px solid var(--border-primary);border-radius:8px;margin-bottom:12px;">
      <div style="display:flex;justify-content:space-between;align-items:start;">
        <div style="flex:1;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
            <span style="font-size:20px;">📍</span>
            <strong style="font-size:16px;">${escapeHtml(loc.name)}</strong>
            <span class="badge" style="background:#3b82f6">${escapeHtml(loc.code)}</span>
          </div>
          ${loc.description ? `<p style="font-size:13px;color:var(--text-secondary);margin:8px 0;">${escapeHtml(loc.description)}</p>` : ''}
          <div style="font-size:12px;color:var(--text-secondary);">
            ${loc.items_count || 0} položek
            ${loc.capacity > 0 ? ` • Kapacita: ${loc.capacity}` : ''}
          </div>
        </div>
        <div style="display:flex;gap:8px;">
          <button class="btn-icon" onclick="editLocation(${loc.id})" title="Upravit">
            <svg style="width:16px;height:16px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="btn-icon" onclick="deleteLocation(${loc.id})" title="Smazat">
            <svg style="width:16px;height:16px;stroke:#f87171" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  `).join('');

  document.getElementById('locationsList').innerHTML = html || '<p style="padding:20px;text-align:center;color:var(--text-secondary);">Žádné lokace</p>';
}

function openNewLocationModal() {
  currentItemId = null;
  document.getElementById('modalTitle').textContent = 'Nová lokace';
  document.getElementById('modalBody').innerHTML = renderLocationForm();
  document.getElementById('btnSaveItem').textContent = 'Uložit';
  document.getElementById('btnSaveItem').onclick = saveLocation;
  document.getElementById('itemModal').classList.add('show');
}

function editLocation(locationId) {
  const location = locations.find(l => l.id === locationId);
  if (!location) return;

  currentItemId = locationId;
  document.getElementById('modalTitle').textContent = 'Upravit lokaci';
  document.getElementById('modalBody').innerHTML = renderLocationForm(location);
  document.getElementById('btnSaveItem').textContent = 'Uložit';
  document.getElementById('btnSaveItem').onclick = saveLocation;
  document.getElementById('itemModal').classList.add('show');
}

function renderLocationForm(location = null) {
  return `
    <form id="locationForm">
      <div class="form-group">
        <label>Kód lokace * <small>(např. A-1-B nebo Sklad-Regál-Police)</small></label>
        <input type="text" id="locationCode" value="${location ? escapeHtml(location.code) : ''}" required placeholder="A-1-B" ${location ? 'readonly' : ''}>
      </div>
      <div class="form-group">
        <label>Název *</label>
        <input type="text" id="locationName" value="${location ? escapeHtml(location.name) : ''}" required placeholder="Sklad A, Regál 1, Police B">
      </div>
      <div class="form-group">
        <label>Popis</label>
        <textarea id="locationDescription" rows="3" placeholder="Dodatečné informace...">${location ? escapeHtml(location.description || '') : ''}</textarea>
      </div>
      <div class="form-group">
        <label>Kapacita (volitelné)</label>
        <input type="number" step="0.01" id="locationCapacity" value="${location ? (location.capacity || '') : ''}" placeholder="0">
      </div>
    </form>
  `;
}

async function saveLocation() {
  const code = document.getElementById('locationCode').value.trim();
  const name = document.getElementById('locationName').value.trim();

  if (!code || !name) {
    alert('Vyplňte všechna povinná pole');
    return;
  }

  const locationData = {
    code: code,
    name: name,
    description: document.getElementById('locationDescription').value.trim(),
    capacity: parseFloat(document.getElementById('locationCapacity').value) || 0
  };

  try {
    if (!currentItemId) {
      // Create
      const resp = await fetch('/api/warehouse/locations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(locationData)
      });
      const data = await resp.json();
      if (data.success) {
        addHistory(`Nová lokace: ${name}`);
      } else {
        alert(data.error || 'Chyba při vytváření lokace');
        return;
      }
    } else {
      // Update
      const resp = await fetch(`/api/warehouse/locations/${currentItemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(locationData)
      });
      const data = await resp.json();
      if (data.success) {
        addHistory(`Upravena lokace: ${name}`);
      } else {
        alert(data.error || 'Chyba při úpravě lokace');
        return;
      }
    }

    await loadLocations();
    window.closeModal();
  } catch (e) {
    console.error('Error saving location:', e);
    alert('Chyba při ukládání lokace');
  }
}

async function deleteLocation(locationId) {
  if (!confirm('Opravdu smazat tuto lokaci?')) {
    return;
  }

  try {
    const resp = await fetch(`/api/warehouse/locations/${locationId}`, {
      method: 'DELETE'
    });
    const data = await resp.json();
    if (data.success) {
      addHistory('Smazána lokace');
      await loadLocations();
    } else {
      alert(data.error || 'Chyba při mazání lokace');
    }
  } catch (e) {
    console.error('Error deleting location:', e);
    alert('Chyba při mazání lokace');
  }
}
