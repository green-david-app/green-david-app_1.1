
// Inject explicit "Upravit" buttons next to "Otevřít detail" on job cards
(function(){
  function normalizeDate(s){
    if(!s) return "";
    // accept DD.MM.YYYY as well
    const m = String(s).trim();
    const dmy = m.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
    if(dmy){ const [_,d,mo,y]=dmy; return `${y}-${mo.padStart(2,'0')}-${d.padStart(2,'0')}`; }
    return m;
  }

  async function loadJobIntoForm(id){
    try{
      const r = await fetch(`/api/jobs/${id}`);
      const js = await r.json();
      if(!js || !js.ok) return;
      const job = js.job || {};
      const form = document.getElementById('jobForm');
      if(!form) return;
      // ensure hidden id field exists
      if(!form.querySelector('[name="id"]')){
        const hid = document.createElement('input');
        hid.type='hidden'; hid.name='id'; hid.id='jobId';
        form.prepend(hid);
      }
      form.querySelector('[name="id"]').value = job.id;
      const set = (n,v)=>{ const el=form.querySelector(`[name="${n}"]`); if(el) el.value = v ?? ""; };
      set('title', job.title);
      set('client', job.client);
      set('status', job.status);
      set('city', job.city);
      set('code', job.code);
      set('note', job.note);
      if(form.querySelector('[name="date"]')){
        const iso = (job.date||"").substring(0,10);
        set('date', iso || normalizeDate(job.date));
      }

      // Flag patch mode on form element
      form.dataset.patch = "1";
      const submit = form.querySelector('button[type="submit"], .save');
      if(submit){ submit.textContent = "Uložit změny"; }

      // Add cancel button once
      if(!document.getElementById('cancelEdit')){
        const cancel=document.createElement('button');
        cancel.type='button'; cancel.id='cancelEdit'; cancel.className='btn secondary';
        cancel.textContent='Zrušit úpravy';
        cancel.addEventListener('click', ()=>{
          delete form.dataset.patch;
          form.reset();
          if(form.querySelector('[name="id"]')) form.querySelector('[name="id"]').value="";
          if(submit) submit.textContent = "Přidat zakázku";
        });
        submit && submit.parentNode && submit.parentNode.appendChild(cancel);
      }

      form.scrollIntoView({behavior:'smooth', block:'start'});
    }catch(e){ console.warn(e); }
  }

  function addButtons(){
    // find all "Otevřít detail" buttons and clone their class for the new edit button
    document.querySelectorAll('button, a').forEach(el=>{
      const txt = (el.textContent||'').trim().toLowerCase();
      if(txt === 'otevřít detail' || txt === 'otevrit detail'){
        const card = el.closest('.job, .card, .row, li, div'); // best-effort
        if(!card) return;
        const jid = (card.getAttribute('data-id') || card.querySelector('[data-id]')?.getAttribute('data-id') ||
                     el.getAttribute('data-id') || '').replace(/\D+/g,'');
        if(!jid) return;
        // avoid duplicates
        if(card.querySelector('[data-edit="1"]')) return;
        const btn = document.createElement('button');
        btn.type='button';
        btn.dataset.edit='1';
        btn.dataset.id=jid;
        // copy class from "Otevřít detail" to keep styling identical
        btn.className = el.className || 'btn';
        btn.style.marginLeft = '6px';
        btn.textContent='Upravit';
        el.parentNode.insertBefore(btn, el.nextSibling);
      }
    });
  }

  // Delegate clicks to load form
  document.addEventListener('click', (e)=>{
    const b = e.target.closest('[data-edit="1"]');
    if(!b) return;
    e.preventDefault();
    const id = b.getAttribute('data-id'); if(id) loadJobIntoForm(id);
  });

  // Intercept submit → PATCH when in patch mode
  const form = document.getElementById('jobForm');
  if(form){
    form.addEventListener('submit', async (e)=>{
      if(form.dataset.patch !== "1") return; // normal POST for new
      e.preventDefault();
      const fd = new FormData(form);
      const payload = {};
      payload.id = Number(fd.get('id')||0);
      ['title','client','status','city','code','date','note'].forEach(k=>{
        if(fd.has(k)) payload[k]=fd.get(k)||'';
      });
      if(payload.date) payload.date = normalizeDate(payload.date);
      const r = await fetch('/api/jobs', {method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const js = await r.json();
      if(js && js.ok){
        delete form.dataset.patch;
        (window.reloadJobs || (()=>location.reload()))();
      }else{
        alert('Uložení se nepovedlo');
      }
    }, true);
  }

  // Run once after DOM is ready
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', addButtons);
  } else {
    addButtons();
  }
})();
