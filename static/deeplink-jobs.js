
// Deep-link support for /?tab=jobs&jobId=123 from search results
(function(){
  const qs = new URLSearchParams(location.search);
  const wantTab = qs.get('tab');
  const jobId = qs.get('jobId');

  // Helper: wait for an element to appear
  function waitFor(sel, {timeout=4000, within=document}={}){
    return new Promise((resolve,reject)=>{
      const t0 = +new Date();
      const node = within.querySelector(sel);
      if (node) return resolve(node);
      const obs = new MutationObserver(()=>{
        const n = within.querySelector(sel);
        if (n){ obs.disconnect(); resolve(n); }
        if ((+new Date())-t0>timeout){ obs.disconnect(); reject(new Error("timeout")); }
      });
      obs.observe(within, {childList:true, subtree:true});
      setTimeout(()=>{ if ((+new Date())-t0>timeout){ obs.disconnect(); reject(new Error("timeout")); }}, timeout+50);
    });
  }

  // Fallback modal if UI doesn't have a native "detail" handler
  function ensureModal(){
    if (document.querySelector('.deeplink-modal-backdrop')) return;
    const back = document.createElement('div');
    back.className = 'deeplink-modal-backdrop';
    back.innerHTML = `
      <div class="deeplink-modal" role="dialog" aria-modal="true">
        <header>
          <h3>Detail zakázky</h3>
          <button class="deeplink-close" type="button">Zavřít</button>
        </header>
        <div class="body">
          <div class="content">Načítám…</div>
        </div>
      </div>`;
    document.body.appendChild(back);
    back.addEventListener('click', (e)=>{
      if (e.target===back || e.target.closest('.deeplink-close')){
        back.style.display='none';
        history.replaceState({}, '', location.pathname + (wantTab?`?tab=${encodeURIComponent(wantTab)}`:''));
      }
    });
    return back;
  }

  async function showFallbackDetail(id){
    try{
      const back = ensureModal();
      back.style.display='flex';
      const box = back.querySelector('.content');
      box.textContent = 'Načítám…';
      const res = await fetch(`/api/jobs/${encodeURIComponent(id)}`);
      if (!res.ok) throw new Error('HTTP '+res.status);
      const job = await res.json();
      const kv = (label, key)=>(job[key]!==undefined && job[key]!==null ? `<div><strong>${label}</strong></div><div>${String(job[key])||''}</div>`:'')
      box.innerHTML = `
        <div class="deeplink-kv">
          ${kv('ID','id')}
          ${kv('Název','name') || kv('Zakázka','title')}
          ${kv('Zákazník','customer')}
          ${kv('Stav','status')}
          ${kv('Termín','due_date') || kv('deadline','deadline')}
          ${kv('Adresa','address')}
          ${kv('Poznámka','note')}
        </div>
      `;
    }catch(err){
      console.error('deeplink fallback failed', err);
      alert('Nepodařilo se načíst detail zakázky.');
    }
  }

  async function hydrateJob(id){
    // Try to click the correct row / detail button if present
    try{
      // Heuristics: table row with data-id or text match; or a detail button with data-id
      const tableSel = ['[data-table="jobs"]','table','[role="table"]'].join(',');
      await waitFor(tableSel, {timeout: 2000}).catch(()=>{});

      const row = Array.from(document.querySelectorAll('[data-id], [data-job-id], tr, li, .job-row')).find(el=>{
        const did = el.getAttribute('data-id') || el.getAttribute('data-job-id');
        if (did && String(did)==String(id)) return true;
        const txt = (el.textContent || '').trim();
        return new RegExp(`\b${String(id)}\b`).test(txt);
      });

      // Prefer an explicit "detail" button inside the row
      let btn = row && (row.querySelector('[data-action="detail"], .btn-detail, a[href*="job"], a[href*="detail"]'));
      if (!btn){
        // Try a global button/link that targets this id
        btn = document.querySelector(`[data-id="${CSS.escape(String(id))}"][data-action="detail"], [data-job-id="${CSS.escape(String(id))}"][data-action="detail"]`);
      }

      if (btn){
        btn.dispatchEvent(new MouseEvent('click', {bubbles:true}));
        return true;
      }
    }catch(e){
      console.debug('deeplink click heuristic failed', e);
    }
    return false;
  }

  async function run(){
    // 1) Switch tab if requested
    if (wantTab){
      // Try common tab switchers
      const tabMap = {
        'jobs': ['[data-tab="jobs"]','a[href*="tab=jobs"]','button[name="jobs"]','#tab-jobs'],
        'employees': ['[data-tab="employees"]','a[href*="tab=employees"]','button[name="employees"]','#tab-employees']
      };
      const sels = tabMap[wantTab] || [];
      for (const s of sels){
        const el = document.querySelector(s);
        if (el){ el.click(); break; }
      }
    }

    if (jobId){
      // Give the page a moment to render the list
      setTimeout(async ()=>{
        const clicked = await hydrateJob(jobId);
        if (!clicked){
          // Fallback: show inline modal with fetched data
          showFallbackDetail(jobId);
        }
      }, 300);
    }
  }

  // Defer until DOM ready
  if (document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
