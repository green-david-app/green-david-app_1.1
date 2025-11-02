// Jednoduché přepínání karet
const tabs = document.querySelectorAll('.tab');
const tabEmployees = document.getElementById('tab-employees');
const tabTemps = document.getElementById('tab-temps');
tabs.forEach(t => t.addEventListener('click', () => {
  tabs.forEach(x => x.classList.remove('active'));
  t.classList.add('active');
  const name = t.dataset.tab;
  tabEmployees.classList.toggle('hidden', name !== 'employees');
  tabTemps.classList.toggle('hidden', name !== 'temps');
}));

// BRIGÁDNÍCI
const tbody = document.querySelector('#temps-table tbody');
const modal = document.getElementById('temp-modal');
const form = document.getElementById('temp-form');
const btnAdd = document.getElementById('btn-add-temp');
const btnExport = document.getElementById('btn-export-csv');

let editId = null;

function fmtContact(row) {
  const phone = row.phone ? row.phone : '';
  const email = row.email ? row.email : '';
  return [phone, email].filter(Boolean).join(' · ');
}

function fmtCurrency(x) {
  const n = Number(x || 0);
  return new Intl.NumberFormat('cs-CZ', { style: 'currency', currency: 'CZK', maximumFractionDigits: 0 }).format(n);
}

async function loadTemps() {
  const res = await fetch('/gd/api/temps');
  const rows = await res.json();
  tbody.innerHTML = '';
  for (const r of rows) {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${r.first_name} ${r.last_name}</td>
      <td>${fmtContact(r)}</td>
      <td>${fmtCurrency(r.hourly_rate)}</td>
      <td>${r.active ? 'ano' : 'ne'}</td>
      <td>${r.notes || ''}</td>
      <td style="text-align:right;white-space:nowrap">
        <button data-id="${r.id}" class="btn secondary btn-edit">Upravit</button>
        <button data-id="${r.id}" class="btn secondary btn-del">Smazat</button>
      </td>
    `;
    tbody.appendChild(tr);
  }
  bindRowButtons();
}

function bindRowButtons() {
  document.querySelectorAll('.btn-edit').forEach(b => b.addEventListener('click', onEdit));
  document.querySelectorAll('.btn-del').forEach(b => b.addEventListener('click', onDelete));
}

btnAdd.addEventListener('click', () => {
  editId = null;
  form.reset();
  form.querySelector('[name=hourly_rate]').value = 0;
  form.querySelector('[name=active]').checked = true;
  document.getElementById('modal-title').textContent = 'Nový brigádník';
  modal.showModal();
});

function fillForm(row) {
  form.querySelector('[name=first_name]').value = row.first_name || '';
  form.querySelector('[name=last_name]').value = row.last_name || '';
  form.querySelector('[name=phone]').value = row.phone || '';
  form.querySelector('[name=email]').value = row.email || '';
  form.querySelector('[name=hourly_rate]').value = row.hourly_rate || 0;
  form.querySelector('[name=active]').checked = !!row.active;
  form.querySelector('[name=notes]').value = row.notes || '';
}

async function onEdit(e) {
  const id = e.target.getAttribute('data-id');
  const res = await fetch('/gd/api/temps/' + id);
  if (!res.ok) return alert('Nelze načíst záznam');
  const row = await res.json();
  editId = id;
  document.getElementById('modal-title').textContent = 'Upravit brigádníka';
  fillForm(row);
  modal.showModal();
}

async function onDelete(e) {
  if (!confirm('Opravdu smazat?')) return;
  const id = e.target.getAttribute('data-id');
  const res = await fetch('/gd/api/temps/' + id, { method: 'DELETE' });
  if (!res.ok) return alert('Chyba mazání');
  loadTemps();
}

form.addEventListener('close', () => {
  if (form.returnValue === 'save') submitForm();
});

async function submitForm() {
  const payload = {
    first_name: form.querySelector('[name=first_name]').value.trim(),
    last_name: form.querySelector('[name=last_name]').value.trim(),
    phone: form.querySelector('[name=phone]').value.trim(),
    email: form.querySelector('[name=email]').value.trim(),
    hourly_rate: Number(form.querySelector('[name=hourly_rate]').value || 0),
    active: form.querySelector('[name=active]').checked,
    notes: form.querySelector('[name=notes]').value.trim(),
  };
  let res;
  if (editId) {
    res = await fetch('/gd/api/temps/' + editId, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  } else {
    res = await fetch('/gd/api/temps', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  }
  if (!res.ok) return alert('Chyba ukládání');
  modal.close();
  loadTemps();
}

window.addEventListener('DOMContentLoaded', loadTemps);
