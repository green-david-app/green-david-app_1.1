(function(){
  function qsAll(sel){ return Array.prototype.slice.call(document.querySelectorAll(sel)); }
  async function httpDelete(url){
    const res = await fetch(url, { method: 'DELETE' });
    if(!res.ok){ throw new Error('HTTP '+res.status+' '+(await res.text().catch(()=>''))); }
    return res.json().catch(()=> ({}));
  }
  async function httpPatch(url, patch){
    const res = await fetch(url, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(patch || {})
    });
    if(!res.ok){ throw new Error('HTTP '+res.status+' '+(await res.text().catch(()=>''))); }
    return res.json().catch(()=> ({}));
  }
  async function reloadAfter(promise){
    try{ await promise; location.reload(); }catch(e){ alert('Chyba: '+e.message); }
  }
  window.deleteJob = function(id){
    if(!id){ alert('Chybí ID zakázky'); return; }
    if(!confirm('Opravdu smazat zakázku #'+id+'?')) return;
    reloadAfter(httpDelete(`/api/jobs/${id}`));
  };
  window.updateJobStatus = function(id, newStatus){
    if(!id){ alert('Chybí ID zakázky'); return; }
    const s = (newStatus || prompt('Nový stav (např. "Probíhá", "Dokončeno"):', 'Probíhá')) || '';
    if(!s.trim()) return;
    reloadAfter(httpPatch(`/api/jobs/${id}`, { status: s.trim() }));
  };
  window.deleteCalendarForJob = function(jobId){
    if(!jobId){ alert('Chybí ID zakázky'); return; }
    reloadAfter(httpDelete(`/gd/api/calendar?id=job-${jobId}`));
  };
  function bind(){
    qsAll('[data-action="delete"][data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.deleteJob(btn.getAttribute('data-id'));
      });
    });
    qsAll('.delete-job[data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.deleteJob(btn.getAttribute('data-id'));
      });
    });
    qsAll('a[data-id],button[data-id]').forEach(el=>{
      const t=(el.textContent||'').toLowerCase();
      if(t.includes('smazat')){
        el.addEventListener('click', function(ev){
          ev.preventDefault();
          window.deleteJob(el.getAttribute('data-id'));
        });
      }
    });
    qsAll('[data-action="set-status"][data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.updateJobStatus(btn.getAttribute('data-id'), btn.getAttribute('data-status')||undefined);
      });
    });
    qsAll('[data-action="cal-del"][data-id]').forEach(btn=>{
      btn.addEventListener('click', function(ev){
        ev.preventDefault();
        window.deleteCalendarForJob(btn.getAttribute('data-id'));
      });
    });
  }
  if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', bind); }
  else { bind(); }
})();