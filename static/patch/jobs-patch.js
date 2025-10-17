(function() {
  function ready(fn){ if(document.readyState!=='loading') fn(); else document.addEventListener('DOMContentLoaded',fn); }
  async function http(url, opts = {}){
    const o = { method: 'GET', headers: { 'Content-Type':'application/json' }, credentials: 'same-origin', ...opts };
    if (o.body && typeof o.body !== 'string') o.body = JSON.stringify(o.body);
    const res = await fetch(url, o);
    let data = null; try { data = await res.json(); } catch(_){}
    return data || { ok: res.ok, status: res.status };
  }
  async function deleteJobSmart(id){
    const num = String(id||'').match(/\d+/)?.[0];
    if(!num){ alert('Neplatné ID zakázky.'); return false; }

    // 1) Primární varianta: path
    let r = await http(`/api/jobs/${num}`, { method: 'DELETE' });

    // 404/405 → fallback na query
    if(r && (r.status===404 || r.status===405)){
      r = await http(`/api/jobs?id=${encodeURIComponent(num)}`, { method: 'DELETE' });
      if(!(r && (r.ok || r.status===200))){
        r = await http(`/gd/api/jobs?id=${encodeURIComponent(num)}`, { method: 'DELETE' });
      }
    }

    // Závislosti → dotaz a force
    if(r && r.error==='has_dependencies'){
      const ok = confirm(`Zakázka má navázané položky (výkazy: ${r.timesheets}, úkoly: ${r.tasks}). Smazat vše?`);
      if(ok){
        let r2 = await http(`/api/jobs/${num}?force=1`, { method: 'DELETE' });
        if(!(r2 && (r2.ok || r2.status===200))){
          r2 = await http(`/api/jobs?id=${encodeURIComponent(num)}&force=1`, { method: 'DELETE' });
          if(!(r2 && (r2.ok || r2.status===200))){
            r2 = await http(`/gd/api/jobs?id=${encodeURIComponent(num)}&force=1`, { method: 'DELETE' });
          }
        }
        r = r2;
      }
    }

    if(!(r && (r.ok || r.status===200))){
      console.warn('Mazání selhalo:', r);
      alert(`Nepodařilo se smazat zakázku (chyba: ${(r && (r.error||r.status))||'unknown'})`);
      return false;
    }
    return true;
  }

  // Veřejná funkce
  window.deleteJob = async function(id){
    const ok = await deleteJobSmart(id);
    if(ok){
      if(typeof window.refreshJobsList==='function') await window.refreshJobsList();
      else location.reload();
    }
  };

  // Delegace na tlačítka s atributem data-action="delete-job"
  ready(function(){
    document.addEventListener('click', async (e)=>{
      const el = e.target.closest('[data-action="delete-job"][data-id]');
      if(!el) return;
      e.preventDefault();
      const ok = await deleteJobSmart(el.getAttribute('data-id'));
      if(ok) location.reload();
    });
  });
})();