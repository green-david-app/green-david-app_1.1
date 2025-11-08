
/**
 * calendar-notes-wireup.js
 * Non-invasive binding to existing calendar UI:
 * - finds the "Poznámka" tab by its text
 * - finds the textarea with placeholder "Text poznámky*"
 * - wires "Uložit" button to POST /gd/api/notes (jobId, title from text head, body = text)
 * - renders note pills with the text head and allows delete/edit
 * Requires global currentJobId for the selected day/job context.
 */
(function(){
  function $(sel, root){ return (root||document).querySelector(sel); }
  function $all(sel, root){ return Array.from((root||document).querySelectorAll(sel)); }

  const t = setInterval(()=>{
    // textarea with placeholder "Text poznámky*"
    const textarea = Array.from(document.querySelectorAll('textarea,input')).find(el => {
      const p = (el.getAttribute('placeholder')||'').toLowerCase();
      return p.includes('text poznámky');
    });
    const saveBtn = Array.from(document.querySelectorAll('button')).find(b => (b.textContent||'').trim().toLowerCase()==='uložit');
    const tabNote = Array.from(document.querySelectorAll('*')).find(el => (el.textContent||'').trim()==='Poznámka' && el.tagName!=='OPTION');

    if (!textarea || !saveBtn || !tabNote) return; // keep waiting until UI is ready
    clearInterval(t);

    async function refreshList(){
      try{
        if (typeof currentJobId==='undefined' || !currentJobId) return;
        const res = await fetch(`/gd/api/notes?job_id=${currentJobId}`);
        if(!res.ok) return;
        const data = await res.json();
        // Target list area: try to find the list container above the form (same white card)
        let container = textarea.closest('.card, .panel, .content, .sheet, .modal, body');
        if (!container) container = document.body;
        let list = container.querySelector('#notesListAuto');
        if (!list){
          list = document.createElement('div');
          list.id = 'notesListAuto';
          list.style.margin = '8px 0 12px 0';
          container.firstElementChild ? container.insertBefore(list, container.firstElementChild.nextSibling) : container.appendChild(list);
        }
        list.innerHTML = data.map(n => {
          const head = (n.title && n.title.trim()) ? n.title.trim() : (n.body || '').trim().slice(0,60) || 'Poznámka';
          return `<div class="badge note-chip" data-id="${n.id}" style="display:inline-flex;align-items:center;gap:.5rem;margin:4px;padding:6px 10px;border-radius:9999px;border:1px solid rgba(255,255,255,.2);">
            <span class="chip-text">${head}</span>
            <a href="#" class="chip-edit" style="opacity:.8">Upravit</a>
            <a href="#" class="chip-del" style="opacity:.8">×</a>
          </div>`;
        }).join('');
      }catch(e){ console.warn(e); }
    }

    // Wire Save
    saveBtn.addEventListener('click', async (e)=>{
      // only act when 'Poznámka' tab active (style check by text)
      const activeIsNote = (tabNote.classList.contains('active') || tabNote.getAttribute('aria-selected')==='true' || /Poznámka/.test(tabNote.textContent||''));
      if (!activeIsNote) return; // don't hijack other tabs
      e.preventDefault();
      const text = (textarea.value||'').trim();
      if (!text) return;
      const payload = {
        jobId: typeof currentJobId!=='undefined' ? currentJobId : null,
        text: text,
        title: text.slice(0,60)
      };
      try{
        await fetch('/gd/api/notes', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        textarea.value='';
        refreshList();
      }catch(e){ console.error(e); }
    });

    // Wire delete/edit on chips
    document.addEventListener('click', async (e)=>{
      const del = e.target.closest('.chip-del');
      const edit = e.target.closest('.chip-edit');
      if (!del && !edit) return;
      e.preventDefault();
      const chip = e.target.closest('.note-chip');
      const id = +chip.dataset.id;
      if (del){
        if (!confirm('Smazat poznámku?')) return;
        await fetch(`/gd/api/notes?id=${id}`, { method:'DELETE' });
        chip.remove();
        return;
      }
      if (edit){
        const old = chip.querySelector('.chip-text')?.textContent || '';
        const text = prompt('Upravit poznámku:', old);
        if (text===null) return;
        await fetch('/gd/api/notes', {
          method:'PATCH', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ id, text: text, title: text.slice(0,60) })
        });
        chip.querySelector('.chip-text').textContent = text.slice(0,60) || 'Poznámka';
        return;
      }
    });

    // initial load
    refreshList();
    // reload when day/job changes if host UI exposes a hook
    if (window.reloadNotes) window.addEventListener('dayChanged', refreshList);
  }, 200);
})();
