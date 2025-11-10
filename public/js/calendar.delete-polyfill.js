(() => {
  const origFetch = window.fetch;
  function isTasksDelete(url, opts) {
    try {
      const u = typeof url === 'string' ? url : (url?.url || '');
      const method = (opts?.method || 'GET').toUpperCase();
      return method === 'DELETE' && (/\/gd\/api\/tasks\b/.test(u) || /\/api\/tasks\b/.test(u));
    } catch { return false; }
  }
  window.fetch = async function patchedFetch(url, opts) {
    const res = await origFetch(url, opts);
    if (isTasksDelete(url, opts) && res.status === 404) {
      // Přemapuj na "už smazáno" → chovej se stejně jako 200 OK
      const idMatch = (typeof url === 'string' ? url : url?.url || '').match(/[?&]id=([^&]+)/);
      const id = idMatch ? decodeURIComponent(idMatch[1]) : null;
      const body = JSON.stringify({ ok: true, deleted: id, note: "not_found_treated_as_deleted" });
      return new Response(body, {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    }
    return res;
  };
})();
