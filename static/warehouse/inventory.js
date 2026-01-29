// ====== INVENTORY MODULE ======

let currentInventoryId = null;

async function loadInventories() {
  try {
    const resp = await fetch('/api/warehouse/inventory');
    const data = await resp.json();
    if (data.success) {
      inventories = data.inventories || [];
      renderInventories();
    }
  } catch (e) {
    console.error('Error loading inventories:', e);
  }
}

function renderInventories() {
  const html = inventories.map(inv => {
    const progress = inv.items_count > 0 ? Math.round((inv.counted_items / inv.items_count) * 100) : 0;
    const statusBadge = 
      inv.status === 'in_progress' ? '<span class="badge" style="background:#fb923c">Probíhá</span>' :
      inv.status === 'completed' ? '<span class="badge" style="background:#4ade80">Dokončeno</span>' :
      '<span class="badge" style="background:#6b7280">Zrušeno</span>';

    return `
      <div style="padding:16px;border:1px solid var(--border-primary);border-radius:8px;margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:12px;">
          <div style="flex:1;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span style="font-size:20px;">✅</span>
              <strong style="font-size:16px;">Inventura ${new Date(inv.inventory_date).toLocaleDateString('cs-CZ')}</strong>
              ${statusBadge}
            </div>
            <div style="font-size:12px;color:var(--text-secondary);">
              Započato: ${new Date(inv.started_at).toLocaleString('cs-CZ')}
              ${inv.started_by_name ? ` • ${escapeHtml(inv.started_by_name)}` : ''}
              ${inv.completed_at ? `<br/>Dokončeno: ${new Date(inv.completed_at).toLocaleString('cs-CZ')}` : ''}
            </div>
            ${inv.note ? `<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">💬 ${escapeHtml(inv.note)}</div>` : ''}
          </div>
          <div style="display:flex;gap:8px;">
            ${inv.status === 'in_progress' ? `
              <button class="btn-secondary" onclick="openInventoryDetail(${inv.id})" style="padding:8px 16px;font-size:13px;">
                📋 Pokračovat (${inv.counted_items}/${inv.items_count})
              </button>
            ` : `
              <button class="btn-secondary" onclick="openInventoryDetail(${inv.id})" style="padding:8px 16px;font-size:13px;">
                👁️ Detail
              </button>
            `}
          </div>
        </div>
        
        ${inv.status === 'in_progress' ? `
        <div style="margin-top:8px;">
          <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
            <span>Napočítáno:</span>
            <span>${inv.counted_items} / ${inv.items_count} (${progress}%)</span>
          </div>
          <div style="height:6px;background:var(--bg-secondary);border-radius:3px;overflow:hidden;">
            <div style="height:100%;background:#B2FBA5;width:${progress}%;transition:width 0.3s;"></div>
          </div>
        </div>
        ` : ''}
      </div>
    `;
  }).join('');

  document.getElementById('inventoriesList').innerHTML = html || '<p style="padding:20px;text-align:center;color:var(--text-secondary);">Žádné inventury</p>';
}

async function startNewInventory() {
  const note = prompt('Poznámka k inventuře (volitelné):');
  
  try {
    const resp = await fetch('/api/warehouse/inventory/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        note: note || ''
      })
    });

    const data = await resp.json();
    if (data.success) {
      addHistory('Spuštěna nová inventura');
      await loadInventories();
      
      // Open detail immediately
      openInventoryDetail(data.inventory_id);
    } else {
      alert(data.error || 'Chyba při spouštění inventury');
    }
  } catch (e) {
    console.error('Error starting inventory:', e);
    alert('Chyba při spouštění inventury');
  }
}

async function openInventoryDetail(inventoryId) {
  currentInventoryId = inventoryId;
  const inventory = inventories.find(i => i.id === inventoryId);
  if (!inventory) return;

  try {
    const resp = await fetch(`/api/warehouse/inventory/${inventoryId}/items`);
    const data = await resp.json();
    if (data.success) {
      document.getElementById('modalTitle').textContent = `Inventura ${new Date(inventory.inventory_date).toLocaleDateString('cs-CZ')}`;
      document.getElementById('modalBody').innerHTML = renderInventoryDetail(inventory, data.items);
      
      if (inventory.status === 'in_progress') {
        document.getElementById('btnSaveItem').textContent = '✅ Dokončit inventuru';
        document.getElementById('btnSaveItem').onclick = completeInventoryModal;
      } else {
        document.getElementById('btnSaveItem').style.display = 'none';
      }
      
      document.getElementById('itemModal').classList.add('show');
    }
  } catch (e) {
    console.error('Error loading inventory detail:', e);
    alert('Chyba při načítání inventury');
  }
}

function renderInventoryDetail(inventory, items) {
  const isActive = inventory.status === 'in_progress';
  const counted = items.filter(i => i.counted_qty !== null).length;
  const total = items.length;

  return `
    <div style="margin-bottom:16px;padding:12px;background:rgba(178,251,165,0.1);border-radius:8px;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:13px;color:var(--text-secondary);">Status</div>
          <div style="font-size:16px;font-weight:600;color:#B2FBA5;margin-top:2px;">
            ${counted} / ${total} položek napočítáno (${Math.round(counted/total*100)}%)
          </div>
        </div>
        ${isActive ? `
        <button class="btn-secondary" onclick="autoFillAllAsExpected()" style="font-size:13px;">
          ⚡ Předvyplnit vše
        </button>
        ` : ''}
      </div>
    </div>

    <div style="max-height:500px;overflow-y:auto;">
      ${items.map(item => renderInventoryItemRow(item, isActive)).join('')}
    </div>
  `;
}

function renderInventoryItemRow(item, isActive) {
  const isCounted = item.counted_qty !== null;
  const difference = isCounted ? item.difference : 0;
  const diffClass = difference > 0 ? 'difference-positive' : difference < 0 ? 'difference-negative' : '';

  return `
    <div class="inventory-row ${isCounted ? 'counted' : ''} ${diffClass}">
      <div>
        <div style="font-weight:500;font-size:13px;">${escapeHtml(item.item_name)}</div>
        <div style="font-size:11px;color:var(--text-secondary);">
          ${item.sku ? `SKU: ${escapeHtml(item.sku)} • ` : ''}
          ${escapeHtml(item.category || '')}
          ${item.location ? ` • 📍 ${escapeHtml(item.location)}` : ''}
        </div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:11px;color:var(--text-secondary);">Očekáváno</div>
        <div style="font-weight:500;">${item.expected_qty} ${escapeHtml(item.item_unit)}</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:11px;color:var(--text-secondary);">Napočítáno</div>
        ${isActive && !isCounted ? `
        <input type="number" step="0.01" id="counted_${item.id}" 
               placeholder="0" 
               style="width:80px;text-align:center;padding:4px 8px;border:1px solid var(--border-primary);border-radius:4px;background:var(--bg-primary);"
               onchange="updateInventoryItem(${item.id}, this.value)">
        ` : `
        <div style="font-weight:500;">${item.counted_qty !== null ? item.counted_qty : '-'} ${escapeHtml(item.item_unit)}</div>
        `}
      </div>
      <div style="text-align:center;">
        <div style="font-size:11px;color:var(--text-secondary);">Rozdíl</div>
        ${isCounted ? `
        <div style="font-weight:600;color:${difference > 0 ? '#4ade80' : difference < 0 ? '#f87171' : 'var(--text-primary)'};">
          ${difference > 0 ? '+' : ''}${difference} ${escapeHtml(item.item_unit)}
        </div>
        ` : `<div>-</div>`}
      </div>
      <div style="text-align:center;">
        ${isCounted ? '✅' : isActive ? '⏳' : '-'}
      </div>
    </div>
  `;
}

async function updateInventoryItem(itemId, countedValue) {
  const countedQty = parseFloat(countedValue);
  if (isNaN(countedQty)) {
    alert('Neplatná hodnota');
    return;
  }

  try {
    const resp = await fetch(`/api/warehouse/inventory/items/${itemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        counted_qty: countedQty
      })
    });

    const data = await resp.json();
    if (data.success) {
      // Refresh detail
      openInventoryDetail(currentInventoryId);
    } else {
      alert(data.error || 'Chyba při ukládání');
    }
  } catch (e) {
    console.error('Error updating inventory item:', e);
    alert('Chyba při ukládání');
  }
}

function autoFillAllAsExpected() {
  if (!confirm('Předvyplnit všechny položky očekávaným množstvím?')) {
    return;
  }

  // Get all inputs and fill with expected values
  const inputs = document.querySelectorAll('[id^="counted_"]');
  inputs.forEach(input => {
    const row = input.closest('.inventory-row');
    const expectedText = row.querySelector('div:nth-child(2) > div:nth-child(2)').textContent.trim();
    const expectedQty = parseFloat(expectedText);
    if (!isNaN(expectedQty)) {
      input.value = expectedQty;
      const itemId = parseInt(input.id.replace('counted_', ''));
      updateInventoryItem(itemId, expectedQty);
    }
  });
}

async function completeInventoryModal() {
  if (!confirm('Opravdu dokončit inventuru? Všechny rozdíly budou aplikovány do skladových stavů.')) {
    return;
  }

  try {
    const resp = await fetch(`/api/warehouse/inventory/${currentInventoryId}/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });

    const data = await resp.json();
    if (data.success) {
      addHistory(`Inventura dokončena (${data.adjustments_count} úprav)`);
      await loadInventories();
      await loadItems();
      await loadStats();
      window.closeModal();
      
      if (window.showToast) {
        window.showToast(`Inventura dokončena. Aplikováno ${data.adjustments_count} úprav.`, 'success');
      }
    } else {
      alert(data.error || 'Chyba při dokončování inventury');
    }
  } catch (e) {
    console.error('Error completing inventory:', e);
    alert('Chyba při dokončování inventury');
  }
}
