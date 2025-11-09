/* calendar-notes-patch.js (enhanced) */
(function(){
  const form = document.querySelector('#noteForm');
  const titleEl = document.querySelector('#noteTitle');
  const bodyEl = document.querySelector('#noteBody');
  const list = document.querySelector('#notesList');
  if (!form || !list) return;

  async function loadNotes() {
    if (typeof currentJobId === 'undefined' || !currentJobId) return;
    const res = await fetch(`/gd/api/notes?job_id=${currentJobId}`);
    if (!res.ok) return;
    const data = await res.json();
    list.innerHTML = data.map(n => `
      <li class="note-item" data-id="${n.id}">
        <div class="note-head">
          <strong>${n.title || 'Bez titulku'}</strong>
          <span style="float:right; gap:.5rem">
            <a href="#" data-id="${n.id}" class="edit-note">Upravit</a>
            &nbsp;|&nbsp;
            <a href="#" data-id="${n.id}" data-pinned="${n.pinned}" class="pin-note">
              ${n.pinned ? 'Odepnout' : 'Připnout'}
            </a>
            &nbsp;|&nbsp;
            <a href="#" data-id="${n.id}" class="del-note">Smazat</a>
          </span>
        </div>
        ${n.body ? `<div class="note-body">${String(n.body).replace(/\n/g,'<br>')}</div>` : ''}
      </li>
    `).join('');
  }

  form.addEventListener('submit', async (e) => {
    if(window.__noteSubmitting){ e.preventDefault(); return; }
    window.__noteSubmitting = true;
    try {
    e.preventDefault();
    if (typeof currentJobId === 'undefined' || !currentJobId) return;
    const payload = {
      jobId: currentJobId,
      title: (titleEl?.value || '').trim(),
      body: (bodyEl?.value || '').trim()
    };
    await fetch('/gd/api/notes', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    if (titleEl) titleEl.value='';
    if (bodyEl) bodyEl.value='';
    loadNotes();
    } finally { window.__noteSubmitting = false; }
  });

  list.addEventListener('click', async (e) => {
    const a = e.target.closest('a');
    if (!a) return;
    e.preventDefault();
    const id = +a.dataset.id;
    if (a.classList.contains('del-note')) {
      if (!confirm('Smazat poznámku?')) return;
      await fetch(`/gd/api/notes?id=${id}`, { method:'DELETE' });
    } else if (a.classList.contains('pin-note')) {
      const pinned = a.dataset.pinned === 'true';
      await fetch('/gd/api/notes', {
        method:'PATCH',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ id, pinned: !pinned })
      });
    } else if (a.classList.contains('edit-note')) {
      const li = a.closest('li');
      const oldTitle = li?.querySelector('.note-head strong')?.textContent || '';
      const oldBody = li?.querySelector('.note-body')?.textContent || '';
      const newTitle = prompt('Titulek poznámky:', oldTitle);
      if (newTitle === null) return;
      const newBody = prompt('Text poznámky:', oldBody);
      if (newBody === null) return;
      await fetch('/gd/api/notes', {
        method:'PATCH',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ id, title: newTitle.trim(), body: newBody.trim() })
      });
    }
    loadNotes();
    } finally { window.__noteSubmitting = false; }
  });

  window.reloadNotes = loadNotes;
  setTimeout(loadNotes, 0);
})();
