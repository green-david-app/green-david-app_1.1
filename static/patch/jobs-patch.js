(function() {
  async function http(url, opts = {}) {
    const o = { method: 'GET', headers: { 'Content-Type':'application/json' }, ...opts };
    if (o.body && typeof o.body !== 'string') o.body = JSON.stringify(o.body);
    const res = await fetch(url, o);
    let data = null;
    try { data = await res.json(); } catch(_) {}
    return data || { ok: res.ok, status: res.status };
  }

  async function deleteJobSmart(id) {
    const num = String(id).match(/\d+/)?.[0];
    if (!num) { alert('Špatné ID zakázky.'); return false; }

    // 1) Primárně path varianta
    let r = await http(`/api/jobs/${num}`, { method: 'DELETE' });

    // fallback na 404/405 → zkus query variantu
    if (r && (r.status === 404 || r.status === 405)) {
      r = await http(`/api/jobs?id=${encodeURIComponent(num)}`, { method: 'DELETE' });
    }

    // závislosti → dotaz a force
    if (r && r.error === 'has_dependencies') {
      const ok = confirm(`Zakázka má navázané položky (výkazy: ${r.timesheets}, úkoly: ${r.tasks}). Smazat vše?`);
      if (ok) {
        let r2 = await http(`/api/jobs/${num}?force=1`, { method: 'DELETE' });
        if (!(r2 && (r2.ok || r2.status === 200))) {
          r2 = await http(`/api/jobs?id=${encodeURIComponent(num)}&force=1`, { method: 'DELETE' });
        }
        r = r2;
      }
    }

    if (!(r && (r.ok || r.status === 200))) {
      console.warn('Mazání selhalo:', r);
      alert(`Nepodařilo se smazat zakázku (chyba: ${(r && (r.error || r.status)) || 'unknown'})`);
      return false;
    }
    return true;
  }

  // Obalíme globální deleteJob, pokud existuje:
  const original = window.deleteJob;
  window.deleteJob = async function(id) {
    const ok = await deleteJobSmart(id);
    if (!ok && typeof original === 'function') return original(id);
    if (ok) {
      if (typeof window.refreshJobsList === 'function') await window.refreshJobsList();
      else location.reload();
    }
  };

  // Záložní listener na tlačítka:
  document.addEventListener('click', async (e) => {
    const el = e.target.closest('[data-action="delete-job"][data-id]');
    if (!el) return;
    e.preventDefault();
    const id = el.getAttribute('data-id');
    const ok = await deleteJobSmart(id);
    if (ok) location.reload();
  });
})();