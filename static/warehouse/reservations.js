// ====== RESERVATIONS MODULE ======

async function loadReservations() {
  try {
    const resp = await fetch('/api/warehouse/reservations?status=active');
    const data = await resp.json();
    if (data.success) {
      reservations = data.reservations || [];
      renderReservations();
    }
  } catch (e) {
    console.error('Error loading reservations:', e);
  }
}

function renderReservations() {
  const html = reservations.map(r => {
    const fromDate = new Date(r.reserved_from).toLocaleDateString('cs-CZ');
    const untilDate = new Date(r.reserved_until).toLocaleDateString('cs-CZ');
    const isExpired = new Date(r.reserved_until) < new Date();

    return `
      <div style="padding:12px;border:1px solid var(--border-primary);border-radius:8px;margin-bottom:8px;${isExpired ? 'opacity:0.6;' : ''}">
        <div style="display:flex;justify-content:space-between;align-items:start;">
          <div style="flex:1;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
              <span style="font-size:20px;">🔒</span>
              <strong style="font-size:14px;">${escapeHtml(r.item_name || 'Neznámá položka')}</strong>
              ${isExpired ? '<span class="badge" style="background:#6b7280">Expirováno</span>' : '<span class="badge" style="background:#3b82f6">Aktivní</span>'}
            </div>
            <div style="font-size:12px;color:var(--text-secondary);">
              Množství: <strong>${r.qty} ${escapeHtml(r.item_unit || 'ks')}</strong>
              ${r.job_title ? ` • Zakázka: ${escapeHtml(r.job_title)}` : ''}
              <br/>
              Od: ${fromDate} → Do: ${untilDate}
              ${r.reserved_by_name ? ` • Rezervoval: ${escapeHtml(r.reserved_by_name)}` : ''}
            </div>
            ${r.note ? `<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">💬 ${escapeHtml(r.note)}</div>` : ''}
          </div>
          <div style="display:flex;gap:8px;">
            ${!isExpired ? `
              <button class="btn-icon" onclick="completeReservation(${r.id})" title="Ukončit">
                <svg style="width:16px;height:16px;stroke:#4ade80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </button>
            ` : ''}
            <button class="btn-icon" onclick="cancelReservation(${r.id})" title="Zrušit">
              <svg style="width:16px;height:16px;stroke:#f87171" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('reservationsList').innerHTML = html || '<p style="padding:20px;text-align:center;color:var(--text-secondary);">Žádné aktivní rezervace</p>';
}

function openNewReservationModal() {
  currentItemId = null;
  document.getElementById('modalTitle').textContent = 'Nová rezervace';
  document.getElementById('modalBody').innerHTML = renderReservationForm();
  document.getElementById('btnSaveItem').textContent = 'Rezervovat';
  document.getElementById('btnSaveItem').onclick = saveReservation;
  document.getElementById('itemModal').classList.add('show');
}

function openReservationModalForItem(itemId) {
  const item = items.find(i => i.id === itemId);
  if (!item) return;

  currentItemId = itemId;
  document.getElementById('modalTitle').textContent = `Rezervace: ${item.name}`;
  document.getElementById('modalBody').innerHTML = renderReservationForm(item);
  document.getElementById('btnSaveItem').textContent = 'Rezervovat';
  document.getElementById('btnSaveItem').onclick = saveReservation;
  document.getElementById('itemModal').classList.add('show');
}

function renderReservationForm(item = null) {
  const today = new Date().toISOString().split('T')[0];
  const nextWeek = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  return `
    <form id="reservationForm">
      ${!item ? `
      <div class="form-group">
        <label>Položka *</label>
        <select id="reservationItem" required onchange="updateReservationItemInfo()">
          <option value="">-- Vyberte položku --</option>
          ${items.filter(i => i.qty > 0).map(i => 
            `<option value="${i.id}" data-qty="${i.qty}" data-unit="${i.unit}">${escapeHtml(i.name)} (${i.qty} ${i.unit})</option>`
          ).join('')}
        </select>
      </div>
      ` : `
      <input type="hidden" id="reservationItem" value="${item.id}">
      <div style="margin-bottom:16px;padding:12px;background:rgba(178,251,165,0.1);border-radius:8px;">
        <div style="font-size:13px;color:var(--text-secondary);">Dostupné množství</div>
        <div style="font-size:18px;font-weight:600;color:#B2FBA5;margin-top:4px;" id="availableQty">
          ${item.qty.toFixed(2)} ${escapeHtml(item.unit)}
        </div>
      </div>
      `}
      
      <div class="form-group">
        <label>Množství *</label>
        <input type="number" step="0.01" id="reservationQty" required placeholder="0" oninput="validateReservationQty()">
        <span id="unitLabel" style="font-size:12px;color:var(--text-secondary);">${item ? item.unit : ''}</span>
      </div>

      <div class="form-group">
        <label>Zakázka (volitelné)</label>
        <select id="reservationJob">
          <option value="">-- Bez zakázky --</option>
        </select>
      </div>

      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
        <div class="form-group">
          <label>Rezervace od *</label>
          <input type="date" id="reservationFrom" value="${today}" required>
        </div>
        <div class="form-group">
          <label>Rezervace do *</label>
          <input type="date" id="reservationUntil" value="${nextWeek}" required>
        </div>
      </div>

      <div class="form-group">
        <label>Poznámka</label>
        <textarea id="reservationNote" rows="3" placeholder="Důvod rezervace..."></textarea>
      </div>

      <div id="reservationWarning" style="display:none;padding:12px;background:rgba(251,146,60,0.1);border-radius:8px;margin-top:12px;">
        <p style="font-size:13px;margin:0;color:#fb923c;">⚠️ <span id="reservationWarningText"></span></p>
      </div>
    </form>
  `;
}

function validateReservationQty() {
  const itemSelect = document.getElementById('reservationItem');
  const qtyInput = document.getElementById('reservationQty');
  const warning = document.getElementById('reservationWarning');
  const warningText = document.getElementById('reservationWarningText');

  if (!itemSelect || !qtyInput) return;

  const itemId = parseInt(itemSelect.value);
  const qty = parseFloat(qtyInput.value) || 0;
  const item = items.find(i => i.id === itemId);

  if (!item) return;

  if (qty > item.qty) {
    warning.style.display = 'block';
    warningText.textContent = `Nedostatečné množství. Dostupné: ${item.qty} ${item.unit}`;
  } else if (qty <= 0) {
    warning.style.display = 'block';
    warningText.textContent = 'Množství musí být větší než 0';
  } else {
    warning.style.display = 'none';
  }
}

async function saveReservation() {
  const itemId = parseInt(document.getElementById('reservationItem').value);
  const qty = parseFloat(document.getElementById('reservationQty').value);
  const from = document.getElementById('reservationFrom').value;
  const until = document.getElementById('reservationUntil').value;
  const jobId = document.getElementById('reservationJob')?.value || null;
  const note = document.getElementById('reservationNote').value.trim();

  if (!itemId || !qty || !from || !until) {
    alert('Vyplňte všechna povinná pole');
    return;
  }

  if (new Date(until) < new Date(from)) {
    alert('Datum konce musí být po datu začátku');
    return;
  }

  try {
    const resp = await fetch('/api/warehouse/reservations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        item_id: itemId,
        qty: qty,
        job_id: jobId ? parseInt(jobId) : null,
        reserved_from: from,
        reserved_until: until,
        note: note
      })
    });

    const data = await resp.json();
    if (data.success) {
      const item = items.find(i => i.id === itemId);
      addHistory(`Rezervace: ${item?.name} (${qty} ${item?.unit})`);
      await loadReservations();
      await loadStats();
      window.closeModal();
    } else {
      alert(data.error || 'Chyba při vytváření rezervace');
    }
  } catch (e) {
    console.error('Error creating reservation:', e);
    alert('Chyba při vytváření rezervace');
  }
}

async function completeReservation(reservationId) {
  if (!confirm('Ukončit tuto rezervaci jako splněnou?')) {
    return;
  }

  try {
    const resp = await fetch(`/api/warehouse/reservations/${reservationId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'completed' })
    });

    const data = await resp.json();
    if (data.success) {
      addHistory('Rezervace ukončena');
      await loadReservations();
      await loadStats();
    } else {
      alert(data.error || 'Chyba při ukončování rezervace');
    }
  } catch (e) {
    console.error('Error completing reservation:', e);
    alert('Chyba při ukončování rezervace');
  }
}

async function cancelReservation(reservationId) {
  if (!confirm('Zrušit tuto rezervaci?')) {
    return;
  }

  try {
    const resp = await fetch(`/api/warehouse/reservations/${reservationId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'cancelled' })
    });

    const data = await resp.json();
    if (data.success) {
      addHistory('Rezervace zrušena');
      await loadReservations();
      await loadStats();
    } else {
      alert(data.error || 'Chyba při rušení rezervace');
    }
  } catch (e) {
    console.error('Error cancelling reservation:', e);
    alert('Chyba při rušení rezervace');
  }
}
