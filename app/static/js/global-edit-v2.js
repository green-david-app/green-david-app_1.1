
(function(){
  function qs(s,root){ return (root||document).querySelector(s); }
  function qsa(s,root){ return Array.from((root||document).querySelectorAll(s)); }
  function getParam(n){ return new URLSearchParams(location.search).get(n); }
  function normalizeDate(s){
    if(!s) return "";
    const m = String(s).trim();
    const dmy = m.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
    if(dmy){ const [_,d,mo,y]=dmy; return `${y}-${mo.padStart(2,'0')}-${d.padStart(2,'0')}`; }
    return m;
  }
  async function loadJobIntoForm(id){
    const form = qs('#jobForm'); if(!form) return;
    if(!form.querySelector('[name="id"]')){
      const hid=document.createElement('input'); hid.type='hidden'; hid.name='id'; hid.id='jobId'; form.prepend(hid);
    }
    const r = await fetch(`/api/jobs/${id}`);
    const js = await r.json(); if(!js||!js.ok) return;
    const job = js.job || {};
    const set=(n,v)=>{ const el=form.querySelector(`[name="${n}"]`); if(el) el.value = v ?? ""; };
    set('id', job.id);
    set('title', job.title); set('client', job.client); set('status', job.status);
    set('city', job.city); set('code', job.code); set('note', job.note);
    const d=form.querySelector('[name="date"]'); if(d){ const iso=(job.date||"").substring(0,10); d.value = iso || normalizeDate(job.date); }
    form.dataset.patch="1";
    const submit = form.querySelector('button[type="submit"], .save'); if(submit) submit.textContent = "Uložit změny";
    if(!qs('#cancelEdit')){
      const cancel=document.createElement('button'); cancel.type='button'; cancel.id='cancelEdit'; cancel.className='btn secondary'; cancel.textContent='Zrušit úpravy';
      cancel.addEventListener('click', ()=>{ delete form.dataset.patch; form.reset(); const idEl=form.querySelector('[name="id"]'); if(idEl) idEl.value=""; if(submit) submit.textContent="Přidat zakázku"; });
      submit && submit.parentNode && submit.parentNode.appendChild(cancel);
    }
    form.scrollIntoView({behavior:'smooth', block:'start'});
  }

  // Intercept submit → PATCH
  (function(){
    const form = qs('#jobForm'); if(!form) return;
    form.addEventListener('submit', async (e)=>{
      if(form.dataset.patch !== "1") return;
      e.preventDefault();
      const fd = new FormData(form); const payload={}; payload.id = Number(fd.get('id')||0);
      ['title','client','status','city','code','date','note'].forEach(k=>{ if(fd.has(k)) payload[k]=fd.get(k)||''; });
      if(payload.date) payload.date = normalizeDate(payload.date);
      const r = await fetch('/api/jobs', {method:'PATCH', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
      const js = await r.json();
      if(js && js.ok){ delete form.dataset.patch; (window.reloadJobs || (()=>location.reload()))(); }
      else alert('Uložení se nepovedlo');
    }, true);
  })();

  // LIST: vlož "Upravit" vedle "Otevřít detail"
  function injectOnList(){
    qsa('button, a').forEach(el=>{
      const t=(el.textContent||'').trim().toLowerCase();
      if(t==='otevřít detail' || t==='otevrit detail'){
        const card = el.closest('[data-id], .job, .card, .row, li, div'); if(!card) return;
        // vezmi id z atributu data-id nebo z URL tlačítka/handleru
        let jid = el.getAttribute('data-id') || card.getAttribute('data-id') || '';
        if(!jid){ const m=(el.getAttribute('href')||'').match(/id=(\d+)/); if(m) jid=m[1]; }
        if(!jid){ const mm=(card.innerHTML||'').match(/data-id=["']?(\d+)["']?/); if(mm) jid=mm[1]; }
        jid = (jid.match(/\d+/)||[])[0];
        if(!jid) return;
        if(card.querySelector('[data-edit="1"]')) return;
        const btn = document.createElement('button');
        btn.type='button'; btn.dataset.edit='1'; btn.dataset.id=jid; btn.className=el.className||'btn'; btn.style.marginLeft='6px'; btn.textContent='Upravit';
        el.parentNode.insertBefore(btn, el.nextSibling);
      }
    });
  }

  // DETAIL: přidej "Upravit" přímo do hlavičky k názvu
  function injectOnDetail(){
    const id = getParam('id'); if(!id) return;
    // najdi kontejner s názvem zakázky – první h1/h2/h3 v rámci hlavního panelu
    const titleEl = qs('.job-header h1, .job-header h2, .job-header h3') ||
                    qs('.panel h1, .panel h2, .panel h3') ||
                    qs('.section h1, .section h2, .section h3') ||
                    qs('h1, h2, h3');
    if(!titleEl || titleEl.closest('#gd-edit-injected')) return;
    // vytvoř obal pro zarovnání (nezasahujeme do CSS: inline-block a malý margin)
    const wrap = document.createElement('span'); wrap.id='gd-edit-injected'; wrap.style.marginLeft='8px';
    const btn = document.createElement('button'); btn.type='button'; btn.className='btn'; btn.textContent='Upravit';
    btn.addEventListener('click', ()=>{ location.href='/' + '#edit-'+id; });
    wrap.appendChild(btn);
    titleEl.appendChild(wrap);
  }

  function hashTrigger(){
    const m=(location.hash||'').match(/^#edit-(\d+)$/); if(!m) return;
    setTimeout(()=>loadJobIntoForm(m[1]), 250);
  }

  // delegace kliků pro list
  document.addEventListener('click', (e)=>{
    const b=e.target.closest('[data-edit="1"]'); if(!b) return;
    e.preventDefault(); const id=b.getAttribute('data-id'); if(id) loadJobIntoForm(id);
  });

  function init(){ injectOnList(); injectOnDetail(); hashTrigger(); }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
