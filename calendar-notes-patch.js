
/* calendar-notes-patch.js
   Non-invasive wiring for "Poznámka" tab to /gd/api/notes.
   Include AFTER your existing calendar JS:
   <script src="calendar-notes-patch.js"></script>
*/
(function(){
  const form = document.querySelector('#noteForm');
  const titleEl = document.querySelector('#noteTitle');
  const bodyEl = document.querySelector('#noteBody');
  const list = document.querySelector('#notesList');
  // currentJobId must exist in your page context (same as for tasks)
  if (!form || !list) return;

  async function loadNotes() {
    if (typeof currentJobId === 'undefined' || !currentJobId) return;
    const res = await fetch(`/gd/api/notes?job_id=${currentJobId}`);
    if (!res.ok) return;
    const data = await res.json();
    list.innerHTML = data.map(n => `
      <li class="note-item">
        <div class="note-head">
          <strong>${n.title || 'Bez titulku'}</strong>
          <span style="float:right">
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
    e.preventDefault();
    if (typeof currentJobId === 'undefined' || !currentJobId) return;
    await fetch('/gd/api/notes', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        jobId: currentJobId,
        title: titleEl.value.trim(),
        body: bodyEl.value.trim()
      })
    });
    titleEl.value=''; bodyEl.value='';
    loadNotes();
  });

  list.addEventListener('click', async (e) => {
    const a = e.target.closest('a');
    if (!a) return;
    e.preventDefault();
    const id = +a.dataset.id;
    if (a.classList.contains('del-note')) {
      await fetch(`/gd/api/notes?id=${id}`, { method:'DELETE' });
    } else if (a.classList.contains('pin-note')) {
      const pinned = a.dataset.pinned === 'true';
      await fetch('/gd/api/notes', {
        method:'PATCH',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ id, pinned: !pinned })
      });
    }
    loadNotes();
  });

  // Expose reload if your code wants to call it
  window.reloadNotes = loadNotes;
  // Initial load (in case currentJobId already set)
  setTimeout(loadNotes, 0);
})();
