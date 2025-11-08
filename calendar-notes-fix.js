
(function(){
  const wait = (sel, root=document) => new Promise(res => {
    const n = root.querySelector(sel);
    if (n) return res(n);
    const obs = new MutationObserver(()=>{
      const n2 = root.querySelector(sel);
      if (n2){ obs.disconnect(); res(n2); }
    });
    obs.observe(document.documentElement, {subtree:true, childList:true});
  });

  async function init(){
    const noteTab = await wait('[data-tab="note"], .tab-note, button:contains("Poznámka"), .note-tab');
    const textarea = await wait('textarea[placeholder*="Text poznámky"], input[placeholder*="Text poznámky"], [data-note-input]');
    const saveBtn = await wait('button, .btn, [role="button"]');

    // Helper to get selected day (expects element with data-date or hidden input)
    function getDate(){
      const el = document.querySelector('[data-selected-date]')||document.querySelector('input[name="date"]');
      return el ? (el.value || el.getAttribute('data-selected-date')) : null;
    }

    async function api(path, opts={}){
      const r = await fetch(path, Object.assign({headers:{'Content-Type':'application/json'}}, opts));
      if(!r.ok) throw new Error(await r.text());
      return r.json().catch(()=>({}));
    }

    async function createNote(){
      const text = (textarea.value || textarea.textContent || '').trim();
      if(!text) return;
      const payload = { title: 'Poznámka', description: text, status: 'note' };
      await api('/gd/api/tasks', { method:'POST', body: JSON.stringify(payload) });
      textarea.value = '';
      await refreshList();
    }

    async function refreshList(){
      const list = document.querySelector('[data-day-list]') || document.querySelector('.day-detail ul') || document.querySelector('.day-detail');
      if(!list) return;
      const items = await fetch('/gd/api/tasks').then(r=>r.json());
      // clear current render region only (not the whole page)
      list.innerHTML = '';
      items.filter(i=> (i.title||'').toLowerCase() === 'poznámka' || (i.status||'')==='note').forEach(item=>{
        const li = document.createElement('div');
        li.className = 'note-pill';
        li.dataset.id = item.id;
        const text = item.description || item.title || 'Poznámka';
        li.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 6px; border-bottom:1px solid rgba(255,255,255,.08)">
            <span>${text.replace(/[<>&]/g, s=>({ '<':'&lt;','>':'&gt;','&':'&amp;' }[s]))}</span>
            <div style="display:flex; gap:8px">
              <button class="note-edit" data-id="${item.id}">Upravit</button>
              <button class="note-del" data-id="${item.id}">×</button>
            </div>
          </div>`;
        list.appendChild(li);
      });
    }

    saveBtn.addEventListener('click', e=>{
      const label = (e.target.textContent||'').toLowerCase();
      if(label.includes('uložit')){
        e.preventDefault();
        createNote().catch(err=>console.error('save note failed', err));
      }
    });

    document.addEventListener('click', e=>{
      const del = e.target.closest('.note-del');
      const edit = e.target.closest('.note-edit');
      if(del){
        const id = del.getAttribute('data-id');
        api('/gd/api/tasks?id='+id, { method:'DELETE' }).then(refreshList);
      }else if(edit){
        const id = edit.getAttribute('data-id');
        const pill = edit.closest('.note-pill');
        const oldTxt = pill ? pill.querySelector('span').textContent : '';
        const txt = prompt('Upravit poznámku:', oldTxt);
        if(txt !== null){
          api('/gd/api/tasks', { method:'PATCH', body: JSON.stringify({ id: Number(id), description: txt })}).then(refreshList);
        }
      }
    });

    refreshList();
  }

  // :contains polyfill in querySelector
  (function(){ 
    const oldQuery = Document.prototype.querySelector;
    Document.prototype.querySelector = function(sel){ 
      if(!sel.includes(':contains')) return oldQuery.call(this, sel);
      const m = sel.match(/(.*):contains\(["']?(.*?)["']?\)/);
      if(!m) return oldQuery.call(this, sel);
      const base = m[1]||'*', text = m[2].toLowerCase();
      const nodes = this.querySelectorAll(base);
      for(const n of nodes){ if((n.textContent||'').toLowerCase().includes(text)) return n; }
      return null;
    };
  })();

  init();
})();
