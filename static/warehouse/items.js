// ====== ITEMS MODULE ======

async function loadItems() {
  try {
    const resp = await fetch('/api/items?site=warehouse');
    const data = await resp.json();
    if (data.success) {
      items = (data.items || []).filter(i => !i.status || i.status === 'active');
      renderItems();
      renderHistory();
      renderTopItems();
      
      // Populate location filter
      const locationFilter = document.getElementById('filterLocation');
      const uniqueLocations = [...new Set(items.map(i => i.location).filter(Boolean))];
      const currentValue = locationFilter.value;
      locationFilter.innerHTML = '<option value="">Všechny lokace</option>';
      uniqueLocations.forEach(loc => {
        const opt = document.createElement('option');
        opt.value = loc;
        opt.textContent = loc;
        locationFilter.appendChild(opt);
      });
      locationFilter.value = currentValue;
    }
  } catch (e) {
    console.error('Error loading items:', e);
  }
}

function renderItems() {
  const search = document.getElementById('searchInput').value.toLowerCase();
  const catFilter = document.getElementById('filterCategory').value;
  const statusFilter = document.getElementById('filterStatus').value;
  const locationFilter = document.getElementById('filterLocation').value;

  let filtered = items.filter(i => {
    if (search && !i.name?.toLowerCase().includes(search) && !i.sku?.toLowerCase().includes(search)) {
      return false;
    }
    if (catFilter && i.category !== catFilter) {
      return false;
    }
    if (locationFilter && i.location !== locationFilter) {
      return false;
    }

    const status = getItemStatus(i);
    if (statusFilter === 'in_stock' && status !== 'in_stock') return false;
    if (statusFilter === 'low_stock' && status !== 'low_stock') return false;
    if (statusFilter === 'out_of_stock' && status !== 'out_of_stock') return false;
    if (statusFilter === 'expiring') {
      if (!i.expiration_date) return false;
      const daysToExpiry = getDaysToExpiry(i.expiration_date);
      if (daysToExpiry === null || daysToExpiry > 30) return false;
    }

    return true;
  });

  const html = filtered.map(i => {
    const status = getItemStatus(i);
    const statusBadge = 
      status === 'in_stock' ? '<span class="badge" style="background:#4ade80">Skladem</span>' :
      status === 'low_stock' ? '<span class="badge" style="background:#fb923c">Málo</span>' :
      '<span class="badge" style="background:#f87171">Nedostupné</span>';

    const expiryBadge = getExpiryBadge(i.expiration_date);
    const batchBadge = i.batch_number ? `<span class="badge" style="background:#3b82f6">Šarže: ${escapeHtml(i.batch_number)}</span>` : '';
    const locationBadge = i.location ? `<span class="location-badge">📍 ${escapeHtml(i.location)}</span>` : '';

    return `
      <div class="item-row">
        <div class="item-image">
          ${i.image ? 
            `<img src="${escapeHtml(i.image)}" alt="${escapeHtml(i.name || '')}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;">` :
            `<div style="width:48px;height:48px;background:rgba(178,251,165,0.1);border-radius:6px;display:flex;align-items:center;justify-content:center;color:#B2FBA5;font-size:20px;">📦</div>`
          }
        </div>
        <div class="item-info">
          <h4>${escapeHtml(i.name || '')}</h4>
          <p style="color:var(--text-secondary);">
            ${i.sku ? `SKU: ${escapeHtml(i.sku)} • ` : ''}
            ${escapeHtml(i.category || '')}
          </p>
          ${locationBadge}
          ${batchBadge}
          ${expiryBadge}
        </div>
        <div class="item-quantity">
          <div><strong>${(i.qty || 0).toFixed(2)}</strong> ${escapeHtml(i.unit || 'ks')}</div>
          ${i.reserved_qty && i.reserved_qty > 0 ? 
            `<div style="font-size:10px;color:#f59e0b;margin-top:2px;">
              🔒 ${i.reserved_qty.toFixed(2)} ${escapeHtml(i.unit || 'ks')} rezerv.
            </div>
            <div style="font-size:10px;color:#9fd4a1;">
              ✅ ${(i.qty - i.reserved_qty).toFixed(2)} ${escapeHtml(i.unit || 'ks')} dost.
            </div>` : 
            ''}
        </div>
        <div class="item-price">
          ${(i.price || 0).toLocaleString('cs-CZ')} Kč/${escapeHtml(i.unit || 'ks')}
        </div>
        <div class="item-status">
          ${statusBadge}
        </div>
        <div class="item-actions">
          <button class="btn-icon" onclick="openItemDetail(${i.id})" title="Detail">
            <svg style="width:16px;height:16px;stroke:currentColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="btn-icon" onclick="openMovementModal(${i.id}, 'out')" title="Vyskladnit">
            <svg style="width:16px;height:16px;stroke:#fb923c" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="17 11 12 6 7 11"/>
              <line x1="12" y1="18" x2="12" y2="6"/>
            </svg>
          </button>
          <button class="btn-icon" onclick="openMovementModal(${i.id}, 'in')" title="Naskladnit">
            <svg style="width:16px;height:16px;stroke:#4ade80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="7 13 12 18 17 13"/>
              <line x1="12" y1="6" x2="12" y2="18"/>
            </svg>
          </button>
          <button class="btn-icon" onclick="openItemContextMenu(event, ${i.id})" title="Více">
            ⋮
          </button>
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('itemsList').innerHTML = html || '<p style="padding:20px;text-align:center;color:var(--text-secondary);">Žádné položky</p>';
}

function getItemStatus(item) {
  const qty = item.qty || 0;
  const minStock = item.minStock || 10;

  if (qty <= 0) return 'out_of_stock';
  if (qty < minStock) return 'low_stock';
  return 'in_stock';
}

function getDaysToExpiry(expirationDate) {
  if (!expirationDate) return null;
  try {
    const expiry = new Date(expirationDate);
    const today = new Date();
    const diff = expiry - today;
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  } catch (e) {
    return null;
  }
}

function getExpiryBadge(expirationDate) {
  const days = getDaysToExpiry(expirationDate);
  if (days === null) return '';
  
  if (days < 0) {
    return `<span class="expired-badge">⚠️ Expirováno před ${Math.abs(days)}d</span>`;
  } else if (days <= 30) {
    return `<span class="expiring-badge">⚠️ Expiruje za ${days}d</span>`;
  }
  return '';
}

function renderHistory() {
  const html = history.slice(0, 10).map(h => `
    <div style="padding:8px;border-bottom:1px solid var(--border-primary);">
      <div style="font-size:12px;color:var(--text-primary);">${escapeHtml(h.text)}</div>
      <div style="font-size:11px;color:var(--text-secondary);margin-top:2px;">${escapeHtml(h.time)}</div>
    </div>
  `).join('');
  document.getElementById('historyList').innerHTML = html || '<p style="padding:12px;text-align:center;color:var(--text-secondary);font-size:12px;">Zatím žádné záznamy</p>';
}

function renderTopItems() {
  // Simplified version - in real app, track from movements
  const html = items
    .sort((a, b) => (b.qty || 0) - (a.qty || 0))
    .slice(0, 5)
    .map(i => `
      <div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid var(--border-primary);">
        <div style="font-size:12px;">${escapeHtml(i.name || '')}</div>
        <div style="font-size:12px;color:#B2FBA5;">${(i.qty || 0).toFixed(2)} ${escapeHtml(i.unit || 'ks')}</div>
      </div>
    `).join('');
  document.getElementById('topItemsList').innerHTML = html || '<p style="padding:12px;text-align:center;color:var(--text-secondary);font-size:12px;">Zatím žádné položky</p>';
}

function addHistory(text) {
  history.unshift({
    text: text,
    time: new Date().toLocaleString('cs-CZ')
  });
  if (history.length > 50) history = history.slice(0, 50);
  saveHistory();
  renderHistory();
}

function saveHistory() {
  localStorage.setItem('warehouse_history', JSON.stringify(history));
}

function clearHistory() {
  if (confirm('Opravdu vymazat celou historii?')) {
    history = [];
    saveHistory();
    renderHistory();
  }
}

window.openNewItemModal = function() {
  currentItemId = null;
  document.getElementById('modalTitle').textContent = 'Nová položka';
  document.getElementById('modalBody').innerHTML = renderItemForm();
  document.getElementById('itemModal').classList.add('show');
  loadLocationsForSelect();
}

window.openItemDetail = function(itemId) {
  currentItemId = itemId;
  const item = items.find(i => i.id === itemId);
  if (!item) return;
  
  document.getElementById('modalTitle').textContent = item.name || 'Detail položky';
  document.getElementById('modalBody').innerHTML = renderItemForm(item);
  document.getElementById('itemModal').classList.add('show');
  loadLocationsForSelect();
};

function renderItemForm(item = null) {
  return `
    <form id="itemForm">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Název položky *</label>
          <input type="text" id="itemName" value="${item ? escapeHtml(item.name || '') : ''}" required placeholder="Např. Obklady Rako 30x60 bílé">
        </div>
        <div class="form-group">
          <label>SKU (kód)</label>
          <input type="text" id="itemSku" value="${item ? escapeHtml(item.sku || '') : ''}" placeholder="OBK-001">
        </div>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Kategorie</label>
          <select id="itemCategory" required>
            ${categories.map(c => `<option value="${c}" ${item && item.category === c ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label>Skladová lokace</label>
          <select id="itemLocation">
            <option value="">-- Vyberte lokaci --</option>
            ${locations.map(loc => `<option value="${loc.code}" ${item && item.location === loc.code ? 'selected' : ''}>${loc.code} - ${loc.name}</option>`).join('')}
          </select>
        </div>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Množství</label>
          <input type="number" step="0.01" id="itemQty" value="${item ? (item.qty || 0) : 0}" required>
        </div>
        <div class="form-group">
          <label>Jednotka</label>
          <input type="text" id="itemUnit" value="${item ? escapeHtml(item.unit || 'ks') : 'ks'}" required placeholder="ks, m², kg, atd.">
        </div>
        <div class="form-group">
          <label>Cena za jednotku (Kč)</label>
          <input type="number" step="0.01" id="itemPrice" value="${item ? (item.price || 0) : 0}" placeholder="450">
        </div>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Číslo šarže</label>
          <input type="text" id="itemBatch" value="${item ? escapeHtml(item.batch_number || '') : ''}" placeholder="LOT-2024-001">
        </div>
        <div class="form-group">
          <label>Datum expirace</label>
          <input type="date" id="itemExpiration" value="${item ? (item.expiration_date || '') : ''}">
        </div>
      </div>
      
      <div class="form-group">
        <label>Minimální stav (varování)</label>
        <input type="number" step="0.01" id="itemMinStock" value="${item ? (item.minStock || 10) : 10}" placeholder="10">
      </div>
      
      <div class="form-group">
        <label>URL obrázku</label>
        <input type="url" id="itemImage" value="${item ? escapeHtml(item.image || '') : ''}" placeholder="https://...">
      </div>
      
      <div class="form-group">
        <label>Poznámka</label>
        <textarea id="itemNote" rows="3" placeholder="Dodatečné informace...">${item ? escapeHtml(item.note || '') : ''}</textarea>
      </div>
      
      ${item ? `
      <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border-primary);">
        <h4 style="margin-bottom:12px;">Rychlé akce</h4>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button type="button" class="btn-secondary" onclick="openRenameModal(${item.id})">✏️ Přejmenovat</button>
          <button type="button" class="btn-secondary" onclick="openMergeModal(${item.id})">🔀 Sloučit s jinou</button>
          <button type="button" class="btn-secondary" onclick="openMovementModal(${item.id}, 'in')">➕ Naskladnit</button>
          <button type="button" class="btn-secondary" onclick="openMovementModal(${item.id}, 'out')">➖ Vyskladnit</button>
          <button type="button" class="btn-secondary" onclick="openReservationModalForItem(${item.id})">🔒 Rezervovat</button>
        </div>
      </div>
      ` : ''}
    </form>
  `;
}

async function loadLocationsForSelect() {
  const select = document.getElementById('itemLocation');
  if (!select) return;
  
  const currentValue = select.value;
  select.innerHTML = '<option value="">Bez lokace</option>';
  
  locations.forEach(loc => {
    const opt = document.createElement('option');
    opt.value = loc.code;
    opt.textContent = loc.name;
    select.appendChild(opt);
  });
  
  select.value = currentValue;
}

window.saveItem = async function() {
  const name = document.getElementById('itemName').value.trim();
  if (!name) {
    alert('Název položky je povinný');
    return;
  }

  const itemData = {
    name: name,
    sku: document.getElementById('itemSku').value.trim(),
    category: document.getElementById('itemCategory').value,
    location: document.getElementById('itemLocation').value,
    qty: parseFloat(document.getElementById('itemQty').value) || 0,
    unit: document.getElementById('itemUnit').value.trim() || 'ks',
    price: parseFloat(document.getElementById('itemPrice').value) || 0,
    minStock: parseFloat(document.getElementById('itemMinStock').value) || 10,
    batch_number: document.getElementById('itemBatch').value.trim(),
    expiration_date: document.getElementById('itemExpiration').value,
    image: document.getElementById('itemImage').value.trim(),
    note: document.getElementById('itemNote').value.trim()
  };

  try {
    if (!currentItemId) {
      // Create new item
      const resp = await fetch('/api/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...itemData, site: 'warehouse' })
      });
      const data = await resp.json();
      if (data.success) {
        addHistory(`Nová položka: ${name}`);
      }
    } else {
      // Update existing item
      const resp = await fetch('/api/items', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: currentItemId, ...itemData })
      });
      const data = await resp.json();
      if (data.success) {
        addHistory(`Upravena položka: ${name}`);
      }
    }

    await loadItems();
    await loadStats();
    window.closeModal();
  } catch (e) {
    console.error('Error saving item:', e);
    alert('Chyba při ukládání položky');
  }
};

window.closeModal = function() {
  document.getElementById('itemModal').classList.remove('show');
  currentItemId = null;
};

window.exportData = function() {
  const csv = [
    ['Název', 'SKU', 'Kategorie', 'Lokace', 'Množství', 'Jednotka', 'Cena', 'Šarže', 'Expirace', 'Status'].join(','),
    ...items.map(i => {
      const status = getItemStatus(i);
      return [
        `"${i.name || ''}"`,
        `"${i.sku || ''}"`,
        `"${i.category || ''}"`,
        `"${i.location || ''}"`,
        i.qty || 0,
        `"${i.unit || ''}"`,
        i.price || 0,
        `"${i.batch_number || ''}"`,
        `"${i.expiration_date || ''}"`,
        status === 'in_stock' ? 'Skladem' : status === 'low_stock' ? 'Málo' : 'Nedostupné'
      ].join(',');
    })
  ].join('\n');
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `sklad_export_${new Date().toISOString().slice(0,10)}.csv`;
  link.click();
};

function openRenameModal(itemId) {
  const item = items.find(i => i.id === itemId);
  if (!item) return;
  
  const newName = prompt('Nový název položky:', item.name);
  if (newName && newName.trim() && newName !== item.name) {
    renameItem(itemId, newName.trim());
  }
}

async function renameItem(itemId, newName) {
  try {
    const resp = await fetch(`/api/warehouse/items/${itemId}/rename`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    });
    const data = await resp.json();
    if (data.success) {
      addHistory(`Přejmenováno: ${newName}`);
      await loadItems();
      window.closeModal();
    } else {
      alert(data.error || 'Chyba při přejmenování');
    }
  } catch (e) {
    console.error('Error renaming item:', e);
    alert('Chyba při přejmenování');
  }
}

function openMergeModal(sourceItemId) {
  const sourceItem = items.find(i => i.id === sourceItemId);
  if (!sourceItem) return;
  
  const targetOptions = items
    .filter(i => i.id !== sourceItemId && i.category === sourceItem.category)
    .map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.qty} ${i.unit})</option>`)
    .join('');
  
  if (!targetOptions) {
    alert('Žádné vhodné položky ke sloučení (stejná kategorie)');
    return;
  }
  
  document.getElementById('modalTitle').textContent = `Sloučit: ${sourceItem.name}`;
  document.getElementById('modalBody').innerHTML = `
    <div class="form-group">
      <label>Sloučit do položky:</label>
      <select id="mergeTargetItem" class="form-control">
        <option value="">-- Vyberte cílovou položku --</option>
        ${targetOptions}
      </select>
    </div>
    <div class="form-group">
      <label>Poznámka (volitelné):</label>
      <input type="text" id="mergeNote" class="form-control" placeholder="Důvod sloučení...">
    </div>
    <div style="padding:12px;background:rgba(251,146,60,0.1);border-radius:8px;margin-top:12px;">
      <p style="font-size:13px;margin:0;">⚠️ Tato akce je nevratná. Položka "${sourceItem.name}" bude sloučena do vybrané položky. Množství a všechny pohyby budou přesunuty.</p>
    </div>
  `;
  
  document.getElementById('btnSaveItem').textContent = 'Sloučit';
  document.getElementById('btnSaveItem').onclick = executeMerge;
  document.getElementById('itemModal').classList.add('show');
}

async function executeMerge() {
  const targetId = parseInt(document.getElementById('mergeTargetItem').value);
  if (!targetId) {
    alert('Vyberte cílovou položku');
    return;
  }
  
  const sourceId = currentItemId;
  const note = document.getElementById('mergeNote').value.trim();
  
  if (!confirm('Opravdu sloučit tyto položky? Tato akce je nevratná.')) {
    return;
  }
  
  try {
    const resp = await fetch('/api/warehouse/items/merge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_item_id: sourceId,
        target_item_id: targetId,
        note: note
      })
    });
    const data = await resp.json();
    if (data.success) {
      alert(data.message);
      addHistory(`Sloučeny položky`);
      await loadItems();
      window.closeModal();
    } else {
      alert(data.error || 'Chyba při slučování');
    }
  } catch (e) {
    console.error('Error merging items:', e);
    alert('Chyba při slučování');
  }
}

function openItemContextMenu(event, itemId) {
  event.stopPropagation();
  const item = items.find(i => i.id === itemId);
  if (!item) return;
  
  // Simple context menu - můžeš vylepšit na plnohodnotné menu
  const actions = [
    { label: '✏️ Upravit', action: () => openItemDetail(itemId) },
    { label: '🔀 Sloučit', action: () => openMergeModal(itemId) },
    { label: '📋 Zobrazit pohyby', action: () => showItemMovements(itemId) },
    { label: '🔒 Rezervovat', action: () => openReservationModalForItem(itemId) }
  ];
  
  // For now, just show alert with options
  const choice = prompt(`Akce pro ${item.name}:\n1. Upravit\n2. Sloučit\n3. Pohyby\n4. Rezervovat\n\nZadejte číslo:`);
  const idx = parseInt(choice) - 1;
  if (idx >= 0 && idx < actions.length) {
    actions[idx].action();
  }
}

function showItemMovements(itemId) {
  currentItemId = itemId;
  switchTab('movements');
  // Filter by item - implement in movements.js
  setTimeout(() => {
    if (window.filterMovementsByItem) {
      window.filterMovementsByItem(itemId);
    }
  }, 100);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}const categories = [
  'Stavební materiál',
  'Nářadí',
  'Elektro',
  'Instalatérství',
  'Dokončovací práce',
  'Zahradní technika',
  
  // ROSTLINY - STROMY
  'Rostliny - Listnaté stromy',
  'Rostliny - Jehličnaté stromy',
  'Rostliny - Ovocné stromy',
  
  // ROSTLINY - KEŘE
  'Rostliny - Listnaté keře',
  'Rostliny - Jehličnaté keře',
  'Rostliny - Ovocné keře',
  'Rostliny - Růže',
  
  // ROSTLINY - TRVALKY
  'Rostliny - Trvalky kvetoucí',
  'Rostliny - Trvalky listnáče',
  'Rostliny - Traviny okrasné',
  'Rostliny - Kapradiny',
  
  // ROSTLINY - SPECIÁLNÍ
  'Rostliny - Skalničky',
  'Rostliny - Vodní a mokřadní',
  'Rostliny - Popínavé',
  'Rostliny -Balkonové a truhlíkové',
  'Rostliny - Bylinky',
  'Rostliny - Zelenina',
  
  // ZAHRADNICKÝ MATERIÁL - SUBSTRÁTY
  'Substráty - Zeminy',
  'Substráty - Komposty',
  'Substráty - Rašelina',
  'Substráty - Speciální směsi',
  
  // ZAHRADNICKÝ MATERIÁL - MULČE
  'Mulče - Kůra',
  'Mulče - Štěpka',
  'Mulče - Kamenivo',
  
  // ZAHRADNICKÝ MATERIÁL - HNOJIVA
  'Hnojiva - Organická',
  'Hnojiva - Minerální',
  'Hnojiva - Organominerální',
  'Hnojiva - Speciální',
  
  // ZAHRADNICKÝ MATERIÁL - OCHRANA
  'Ochrana rostlin - Fungicidy',
  'Ochrana rostlin - Insekticidy',
  'Ochrana rostlin - Herbicidy',
  'Ochrana rostlin - Biopreparáty',
  
  // ZAHRADNICKÝ MATERIÁL - OSTATNÍ
  'Semena a osivo',
  'Cibuloviny',
  'Květináče a truhlíky',
  'Zavlažování',
  'Opěry a podpěry',
  'Textilie a fólie',
  'Dekorace zahradní',
  
  'Ostatní'
];

// ====== ITEMS MODULE ======

async function loadItems() {
  try {
    const resp = await fetch('/api/items?site=warehouse');
    const data = await resp.json();
    if (data.success) {
      items = (data.items || []).filter(i => !i.status || i.status === 'active');
      renderItems();
      renderHistory();
      renderTopItems();
      
      // Populate location filter
      const locationFilter = document.getElementById('filterLocation');
      const uniqueLocations = [...new Set(items.map(i => i.location).filter(Boolean))];
      const currentValue = locationFilter.value;
      locationFilter.innerHTML = '<option value="">Všechny lokace</option>';
      uniqueLocations.forEach(loc => {
        const opt = document.createElement('option');
        opt.value = loc;
        opt.textContent = loc;
        locationFilter.appendChild(opt);
      });
      locationFilter.value = currentValue;
    }
  } catch (e) {
    console.error('Error loading items:', e);
  }
}

function renderItems() {
  const search = document.getElementById('searchInput').value.toLowerCase();
  const catFilter = document.getElementById('filterCategory').value;
  const statusFilter = document.getElementById('filterStatus').value;
  const locationFilter = document.getElementById('filterLocation').value;

  let filtered = items.filter(i => {
    if (search && !i.name?.toLowerCase().includes(search) && !i.sku?.toLowerCase().includes(search)) {
      return false;
    }
    if (catFilter && i.category !== catFilter) {
      return false;
    }
    if (locationFilter && i.location !== locationFilter) {
      return false;
    }

    const status = getItemStatus(i);
    if (statusFilter === 'in_stock' && status !== 'in_stock') return false;
    if (statusFilter === 'low_stock' && status !== 'low_stock') return false;
    if (statusFilter === 'out_of_stock' && status !== 'out_of_stock') return false;
    if (statusFilter === 'expiring') {
      if (!i.expiration_date) return false;
      const daysToExpiry = getDaysToExpiry(i.expiration_date);
      if (daysToExpiry === null || daysToExpiry > 30) return false;
    }

    return true;
  });

  const html = filtered.map(i => {
    const status = getItemStatus(i);
    const statusBadge = 
      status === 'in_stock' ? '<span class="badge" style="background:#4ade80">Skladem</span>' :
      status === 'low_stock' ? '<span class="badge" style="background:#fb923c">Málo</span>' :
      '<span class="badge" style="background:#f87171">Nedostupné</span>';

    const expiryBadge = getExpiryBadge(i.expiration_date);
    const batchBadge = i.batch_number ? `<span class="badge" style="background:#3b82f6">Šarže: ${escapeHtml(i.batch_number)}</span>` : '';
    const locationBadge = i.location ? `<span class="location-badge">📍 ${escapeHtml(i.location)}</span>` : '';

    return `
      <div class="item-row">
        <div class="item-image">
          ${i.image ? 
            `<img src="${escapeHtml(i.image)}" alt="${escapeHtml(i.name || '')}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;">` :
            `<div style="width:48px;height:48px;background:rgba(178,251,165,0.1);border-radius:6px;display:flex;align-items:center;justify-content:center;color:#B2FBA5;font-size:20px;">📦</div>`
          }
        </div>
        <div class="item-info">
          <h4>${escapeHtml(i.name || '')}</h4>
          <p style="color:var(--text-secondary);">
            ${i.sku ? `SKU: ${escapeHtml(i.sku)} • ` : ''}
            ${escapeHtml(i.category || '')}
          </p>
          ${locationBadge}
          ${batchBadge}
          ${expiryBadge}
        </div>
        <div class="item-quantity">
          <div><strong>${(i.qty || 0).toFixed(2)}</strong> ${escapeHtml(i.unit || 'ks')}</div>
          ${i.reserved_qty && i.reserved_qty > 0 ? 
            `<div style="font-size:10px;color:#f59e0b;margin-top:2px;">
              🔒 ${i.reserved_qty.toFixed(2)} ${escapeHtml(i.unit || 'ks')} rezerv.
            </div>
            <div style="font-size:10px;color:#9fd4a1;">
              ✅ ${(i.qty - i.reserved_qty).toFixed(2)} ${escapeHtml(i.unit || 'ks')} dost.
            </div>` : 
            ''}
        </div>
        <div class="item-price">
          ${(i.price || 0).toLocaleString('cs-CZ')} Kč/${escapeHtml(i.unit || 'ks')}
        </div>
        <div class="item-status">
          ${statusBadge}
        </div>
        <div class="item-actions">
          <button class="btn-icon" onclick="openItemDetail(${i.id})" title="Detail">
            <svg style="width:16px;height:16px;stroke:currentColor" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
          </button>
          <button class="btn-icon" onclick="openMovementModal(${i.id}, 'out')" title="Vyskladnit">
            <svg style="width:16px;height:16px;stroke:#fb923c" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="17 11 12 6 7 11"/>
              <line x1="12" y1="18" x2="12" y2="6"/>
            </svg>
          </button>
          <button class="btn-icon" onclick="openMovementModal(${i.id}, 'in')" title="Naskladnit">
            <svg style="width:16px;height:16px;stroke:#4ade80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="7 13 12 18 17 13"/>
              <line x1="12" y1="6" x2="12" y2="18"/>
            </svg>
          </button>
          <button class="btn-icon" onclick="openItemContextMenu(event, ${i.id})" title="Více">
            ⋮
          </button>
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('itemsList').innerHTML = html || '<p style="padding:20px;text-align:center;color:var(--text-secondary);">Žádné položky</p>';
}

function getItemStatus(item) {
  const qty = item.qty || 0;
  const minStock = item.minStock || 10;

  if (qty <= 0) return 'out_of_stock';
  if (qty < minStock) return 'low_stock';
  return 'in_stock';
}

function getDaysToExpiry(expirationDate) {
  if (!expirationDate) return null;
  try {
    const expiry = new Date(expirationDate);
    const today = new Date();
    const diff = expiry - today;
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  } catch (e) {
    return null;
  }
}

function getExpiryBadge(expirationDate) {
  const days = getDaysToExpiry(expirationDate);
  if (days === null) return '';
  
  if (days < 0) {
    return `<span class="expired-badge">⚠️ Expirováno před ${Math.abs(days)}d</span>`;
  } else if (days <= 30) {
    return `<span class="expiring-badge">⚠️ Expiruje za ${days}d</span>`;
  }
  return '';
}

function renderHistory() {
  const html = history.slice(0, 10).map(h => `
    <div style="padding:8px;border-bottom:1px solid var(--border-primary);">
      <div style="font-size:12px;color:var(--text-primary);">${escapeHtml(h.text)}</div>
      <div style="font-size:11px;color:var(--text-secondary);margin-top:2px;">${escapeHtml(h.time)}</div>
    </div>
  `).join('');
  document.getElementById('historyList').innerHTML = html || '<p style="padding:12px;text-align:center;color:var(--text-secondary);font-size:12px;">Zatím žádné záznamy</p>';
}

function renderTopItems() {
  // Simplified version - in real app, track from movements
  const html = items
    .sort((a, b) => (b.qty || 0) - (a.qty || 0))
    .slice(0, 5)
    .map(i => `
      <div style="display:flex;justify-content:space-between;padding:8px;border-bottom:1px solid var(--border-primary);">
        <div style="font-size:12px;">${escapeHtml(i.name || '')}</div>
        <div style="font-size:12px;color:#B2FBA5;">${(i.qty || 0).toFixed(2)} ${escapeHtml(i.unit || 'ks')}</div>
      </div>
    `).join('');
  document.getElementById('topItemsList').innerHTML = html || '<p style="padding:12px;text-align:center;color:var(--text-secondary);font-size:12px;">Zatím žádné položky</p>';
}

function addHistory(text) {
  history.unshift({
    text: text,
    time: new Date().toLocaleString('cs-CZ')
  });
  if (history.length > 50) history = history.slice(0, 50);
  saveHistory();
  renderHistory();
}

function saveHistory() {
  localStorage.setItem('warehouse_history', JSON.stringify(history));
}

function clearHistory() {
  if (confirm('Opravdu vymazat celou historii?')) {
    history = [];
    saveHistory();
    renderHistory();
  }
}


window.openItemDetail = function(itemId) {
  currentItemId = itemId;
  const item = items.find(i => i.id === itemId);
  if (!item) return;
  
  document.getElementById('modalTitle').textContent = item.name || 'Detail položky';
  document.getElementById('modalBody').innerHTML = renderItemForm(item);
  document.getElementById('itemModal').classList.add('show');
  loadLocationsForSelect();
};

function renderItemForm(item = null) {
  return `
    <form id="itemForm">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Název položky *</label>
          <input type="text" id="itemName" value="${item ? escapeHtml(item.name || '') : ''}" required placeholder="Např. Obklady Rako 30x60 bílé">
        </div>
        <div class="form-group">
          <label>SKU (kód)</label>
          <input type="text" id="itemSku" value="${item ? escapeHtml(item.sku || '') : ''}" placeholder="OBK-001">
        </div>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Kategorie</label>
          <select id="itemCategory" required>
            ${categories.map(c => `<option value="${c}" ${item && item.category === c ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
        </div>
        <div class="form-group">
          <label>Skladová lokace</label>
          <select id="itemLocation">
        <option value="">-- Vyberte lokaci --</option>
        ${locations.map(loc => `<option value="${loc.code}">${loc.code} - ${loc.name}</option>`).join('')}
      </select>
        </div>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Množství</label>
          <input type="number" step="0.01" id="itemQty" value="${item ? (item.qty || 0) : 0}" required>
        </div>
        <div class="form-group">
          <label>Jednotka</label>
          <input type="text" id="itemUnit" value="${item ? escapeHtml(item.unit || 'ks') : 'ks'}" required placeholder="ks, m², kg, atd.">
        </div>
        <div class="form-group">
          <label>Cena za jednotku (Kč)</label>
          <input type="number" step="0.01" id="itemPrice" value="${item ? (item.price || 0) : 0}" placeholder="450">
        </div>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Číslo šarže</label>
          <input type="text" id="itemBatch" value="${item ? escapeHtml(item.batch_number || '') : ''}" placeholder="LOT-2024-001">
        </div>
        <div class="form-group">
          <label>Datum expirace</label>
          <input type="date" id="itemExpiration" value="${item ? (item.expiration_date || '') : ''}">
        </div>
      </div>
      
      <div class="form-group">
        <label>Minimální stav (varování)</label>
        <input type="number" step="0.01" id="itemMinStock" value="${item ? (item.minStock || 10) : 10}" placeholder="10">
      </div>
      
      <div class="form-group">
        <label>URL obrázku</label>
        <input type="url" id="itemImage" value="${item ? escapeHtml(item.image || '') : ''}" placeholder="https://...">
      </div>
      
      <div class="form-group">
        <label>Poznámka</label>
        <textarea id="itemNote" rows="3" placeholder="Dodatečné informace...">${item ? escapeHtml(item.note || '') : ''}</textarea>
      </div>
      
      ${item ? `
      <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border-primary);">
        <h4 style="margin-bottom:12px;">Rychlé akce</h4>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <button type="button" class="btn-secondary" onclick="openRenameModal(${item.id})">✏️ Přejmenovat</button>
          <button type="button" class="btn-secondary" onclick="openMergeModal(${item.id})">🔀 Sloučit s jinou</button>
          <button type="button" class="btn-secondary" onclick="openMovementModal(${item.id}, 'in')">➕ Naskladnit</button>
          <button type="button" class="btn-secondary" onclick="openMovementModal(${item.id}, 'out')">➖ Vyskladnit</button>
          <button type="button" class="btn-secondary" onclick="openReservationModalForItem(${item.id})">🔒 Rezervovat</button>
        </div>
      </div>
      ` : ''}
    </form>
  `;
}

async function loadLocationsForSelect() {
  const select = document.getElementById('itemLocation');
  if (!select) return;
  
  const currentValue = select.value;
  select.innerHTML = '<option value="">Bez lokace</option>';
  
  locations.forEach(loc => {
    const opt = document.createElement('option');
    opt.value = loc.code;
    opt.textContent = loc.name;
    select.appendChild(opt);
  });
  
  select.value = currentValue;
}

window.saveItem = async function() {
  const name = document.getElementById('itemName').value.trim();
  if (!name) {
    alert('Název položky je povinný');
    return;
  }

  const itemData = {
    name: name,
    sku: document.getElementById('itemSku').value.trim(),
    category: document.getElementById('itemCategory').value,
    location: document.getElementById('itemLocation').value,
    qty: parseFloat(document.getElementById('itemQty').value) || 0,
    unit: document.getElementById('itemUnit').value.trim() || 'ks',
    price: parseFloat(document.getElementById('itemPrice').value) || 0,
    minStock: parseFloat(document.getElementById('itemMinStock').value) || 10,
    batch_number: document.getElementById('itemBatch').value.trim(),
    expiration_date: document.getElementById('itemExpiration').value,
    image: document.getElementById('itemImage').value.trim(),
    note: document.getElementById('itemNote').value.trim()
  };

  try {
    if (!currentItemId) {
      // Create new item
      const resp = await fetch('/api/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...itemData, site: 'warehouse' })
      });
      const data = await resp.json();
      if (data.success) {
        addHistory(`Nová položka: ${name}`);
      }
    } else {
      // Update existing item
      const resp = await fetch('/api/items', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: currentItemId, ...itemData })
      });
      const data = await resp.json();
      if (data.success) {
        addHistory(`Upravena položka: ${name}`);
      }
    }

    await loadItems();
    await loadStats();
    window.closeModal();
  } catch (e) {
    console.error('Error saving item:', e);
    alert('Chyba při ukládání položky');
  }
};

window.closeModal = function() {
  document.getElementById('itemModal').classList.remove('show');
  currentItemId = null;
};

window.exportData = function() {
  const csv = [
    ['Název', 'SKU', 'Kategorie', 'Lokace', 'Množství', 'Jednotka', 'Cena', 'Šarže', 'Expirace', 'Status'].join(','),
    ...items.map(i => {
      const status = getItemStatus(i);
      return [
        `"${i.name || ''}"`,
        `"${i.sku || ''}"`,
        `"${i.category || ''}"`,
        `"${i.location || ''}"`,
        i.qty || 0,
        `"${i.unit || ''}"`,
        i.price || 0,
        `"${i.batch_number || ''}"`,
        `"${i.expiration_date || ''}"`,
        status === 'in_stock' ? 'Skladem' : status === 'low_stock' ? 'Málo' : 'Nedostupné'
      ].join(',');
    })
  ].join('\n');
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `sklad_export_${new Date().toISOString().slice(0,10)}.csv`;
  link.click();
};

function openRenameModal(itemId) {
  const item = items.find(i => i.id === itemId);
  if (!item) return;
  
  const newName = prompt('Nový název položky:', item.name);
  if (newName && newName.trim() && newName !== item.name) {
    renameItem(itemId, newName.trim());
  }
}

async function renameItem(itemId, newName) {
  try {
    const resp = await fetch(`/api/warehouse/items/${itemId}/rename`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    });
    const data = await resp.json();
    if (data.success) {
      addHistory(`Přejmenováno: ${newName}`);
      await loadItems();
      window.closeModal();
    } else {
      alert(data.error || 'Chyba při přejmenování');
    }
  } catch (e) {
    console.error('Error renaming item:', e);
    alert('Chyba při přejmenování');
  }
}

function openMergeModal(sourceItemId) {
  const sourceItem = items.find(i => i.id === sourceItemId);
  if (!sourceItem) return;
  
  const targetOptions = items
    .filter(i => i.id !== sourceItemId && i.category === sourceItem.category)
    .map(i => `<option value="${i.id}">${escapeHtml(i.name)} (${i.qty} ${i.unit})</option>`)
    .join('');
  
  if (!targetOptions) {
    alert('Žádné vhodné položky ke sloučení (stejná kategorie)');
    return;
  }
  
  document.getElementById('modalTitle').textContent = `Sloučit: ${sourceItem.name}`;
  document.getElementById('modalBody').innerHTML = `
    <div class="form-group">
      <label>Sloučit do položky:</label>
      <select id="mergeTargetItem" class="form-control">
        <option value="">-- Vyberte cílovou položku --</option>
        ${targetOptions}
      </select>
    </div>
    <div class="form-group">
      <label>Poznámka (volitelné):</label>
      <input type="text" id="mergeNote" class="form-control" placeholder="Důvod sloučení...">
    </div>
    <div style="padding:12px;background:rgba(251,146,60,0.1);border-radius:8px;margin-top:12px;">
      <p style="font-size:13px;margin:0;">⚠️ Tato akce je nevratná. Položka "${sourceItem.name}" bude sloučena do vybrané položky. Množství a všechny pohyby budou přesunuty.</p>
    </div>
  `;
  
  document.getElementById('btnSaveItem').textContent = 'Sloučit';
  document.getElementById('btnSaveItem').onclick = executeMerge;
  document.getElementById('itemModal').classList.add('show');
}

async function executeMerge() {
  const targetId = parseInt(document.getElementById('mergeTargetItem').value);
  if (!targetId) {
    alert('Vyberte cílovou položku');
    return;
  }
  
  const sourceId = currentItemId;
  const note = document.getElementById('mergeNote').value.trim();
  
  if (!confirm('Opravdu sloučit tyto položky? Tato akce je nevratná.')) {
    return;
  }
  
  try {
    const resp = await fetch('/api/warehouse/items/merge', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_item_id: sourceId,
        target_item_id: targetId,
        note: note
      })
    });
    const data = await resp.json();
    if (data.success) {
      alert(data.message);
      addHistory(`Sloučeny položky`);
      await loadItems();
      window.closeModal();
    } else {
      alert(data.error || 'Chyba při slučování');
    }
  } catch (e) {
    console.error('Error merging items:', e);
    alert('Chyba při slučování');
  }
}

function openItemContextMenu(event, itemId) {
  event.stopPropagation();
  const item = items.find(i => i.id === itemId);
  if (!item) return;
  
  // Simple context menu - můžeš vylepšit na plnohodnotné menu
  const actions = [
    { label: '✏️ Upravit', action: () => openItemDetail(itemId) },
    { label: '🔀 Sloučit', action: () => openMergeModal(itemId) },
    { label: '📋 Zobrazit pohyby', action: () => showItemMovements(itemId) },
    { label: '🔒 Rezervovat', action: () => openReservationModalForItem(itemId) }
  ];
  
  // For now, just show alert with options
  const choice = prompt(`Akce pro ${item.name}:\n1. Upravit\n2. Sloučit\n3. Pohyby\n4. Rezervovat\n\nZadejte číslo:`);
  const idx = parseInt(choice) - 1;
  if (idx >= 0 && idx < actions.length) {
    actions[idx].action();
  }
}

function showItemMovements(itemId) {
  currentItemId = itemId;
  switchTab('movements');
  // Filter by item - implement in movements.js
  setTimeout(() => {
    if (window.filterMovementsByItem) {
      window.filterMovementsByItem(itemId);
    }
  }, 100);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
