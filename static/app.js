
// --- global fetch helper with 409 force support ---
async function gdFetch(url, opts={}) {
  const res = await fetch(url, Object.assign({headers:{"Content-Type":"application/json"}}, opts));
  if (res.ok) return await (res.headers.get("content-type")?.includes("application/json") ? res.json() : res.text());
  let payload;
  try { payload = await res.json(); } catch { payload = { ok:false, error:`HTTP ${res.status}` }; }
  if (res.status === 409 && payload?.error === "has_dependents" && opts?.gdConfirmForce) {
    const t = payload.tasks ?? 0, ts = payload.timesheets ?? 0;
    const msg = `Položka má navázaná data${t||ts?` (úkoly: ${t}, výkazy: ${ts})`:''}. Chcete ji smazat včetně navázaných záznamů?`;
    if (confirm(msg)) {
      const glue = url.includes('?') ? '&' : '?';
      return gdFetch(url + glue + 'force=1', Object.assign({}, opts, { gdConfirmForce:false }));
    }
  }
  throw new Error(payload?.error || `HTTP ${res.status}`);
}

