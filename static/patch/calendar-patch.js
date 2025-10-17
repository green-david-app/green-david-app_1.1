// helper injected

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
/**
 * green-david calendar patch
 * Version: 2025-10-17a
 */
(function () {
  const VERSION = "2025-10-17a";

  function toast(msg, kind = "ok", timeout = 3500) {
    try {
      const el = document.createElement("div");
      el.className = "gd-toast " + (kind === "error" ? "error" : "ok");
      el.textContent = msg;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), timeout);
    } catch (e) {
      console && console.warn && console.warn("Toast:", msg);
    }
  }

  async function tryFetch(input, init, label) {
    const res = await fetch(input, init);
    if (!res.ok) {
      let detail = "";
      try { detail = await res.text(); } catch (_){}
      const status = res.status;
      console.warn(`[${label}] ${status}`, detail);
      throw new Error(`${label} selhalo (HTTP ${status}) ${detail ? " – " + detail : ""}`);
    }
    return res;
  }

  async function deleteJobCascade(jobId) {
    const id = String(jobId).replace(/^job-/, "").trim();
    if (!id) throw new Error("Neplatné ID zakázky");

    const headers = { "Content-Type": "application/json" };
    const optsDELETE = { method: "DELETE", credentials: "include" };
    const optsDELETEjson = { method: "DELETE", credentials: "include", headers, body: JSON.stringify({ id, cascade: true }) };
    const optsPOST = { method: "POST", credentials: "include", headers, body: JSON.stringify({ id, cascade: true }) };

    try {
      await tryFetch(`/api/jobs/${encodeURIComponent(id)}?cascade=1`, optsDELETE, "DELETE /api/jobs/<id>");
      return true;
    } catch (e1) {}

    try {
      await tryFetch(`/api/jobs?id=${encodeURIComponent(id)}&cascade=1`, optsDELETE, "DELETE /api/jobs?id=");
      return true;
    } catch (e2) {}

    try {
      await tryFetch(`/api/jobs`, optsDELETEjson, "DELETE /api/jobs (JSON body)");
      return true;
    } catch (e3) {}

    try {
      await tryFetch(`/api/jobs/delete`, optsPOST, "POST /api/jobs/delete");
      return true;
    } catch (e4) {
      throw e4;
    }
  }

  async function deleteCalendarRecord(calId) {
    const id = String(calId).trim();
    const url = `/gd/api/calendar?id=${encodeURIComponent(id)}`;
    await tryFetch(url, { method: "DELETE", credentials: "include" }, "DELETE /gd/api/calendar");
    return true;
  }

  async function smartDeleteCalendarItem(id) {
    const isJob = /^job-/.test(id) || /^[0-9]+$/.test(id);

    if (isJob) {
      try {
        await deleteJobCascade(id);
      } catch (e) {
        const msg = String(e && e.message || e);
        if (/HTTP 409/.test(msg)) {
          toast("Zakázku nelze smazat – má navázané záznamy (úkoly/výkazy). Zkusím odstranit jen výskyt v kalendáři…", "error", 4500);
        } else {
          toast("Smazání zakázky selhalo: " + msg, "error", 6000);
        }
      }
    }

    try {
      await deleteCalendarRecord(id);
      toast("Smazáno.", "ok");
    } catch (eCal) {
      const msg = String(eCal && eCal.message || eCal);
      if (/HTTP 409/.test(msg)) {
        toast("Tento záznam je zamčený nebo navázaný – nejdřív odstraň podřízené položky (úkoly, výkazy).", "error", 6000);
      } else {
        toast("Smazání záznamu v kalendáři selhalo: " + msg, "error", 6000);
      }
      throw eCal;
    }

    try {
      if (window.gdReloadCalendarRange) {
        await window.gdReloadCalendarRange();
      } else {
        location.reload();
      }
    } catch (_) {
      location.reload();
    }
  }

  window.gdSmartDeleteCalendarItem = smartDeleteCalendarItem;

  if (typeof window.gdDeleteCalendar === "function") {
    const orig = window.gdDeleteCalendar;
    window.gdDeleteCalendar = async function (id) {
      try {
        await smartDeleteCalendarItem(id);
      } catch (e) {
        try { return await orig(id); } catch (_) {}
      }
    };
  }

  console.info("[calendar-patch.js] loaded", VERSION);
})();
