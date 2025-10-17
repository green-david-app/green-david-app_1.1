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

  async function smartDeleteCalendarItem(itemOrId) {
  const toId = (v) => (typeof v === "string" ? v : (v && (v.id || v._id)) || "");
  const id = toId(itemOrId);
  if (!id) throw new Error("Missing calendar item id");

  const isNumeric = /^\d+$/.test(id);
  const isJob = /^job-(\d+)$/.exec(id);
  const isTask = /^task-(\d+)$/.exec(id);

  const attempt = async (url) => {
    try {
      const res = await fetch(url, { method: "DELETE" });
      if (res.ok) return true;
      if (res.status === 200) return true;
      return false;
    } catch (e) {
      return false;
    }
  };

  if (isNumeric) {
    const pathUrl = `/gd/api/calendar/${id}`;
    const qsUrl = `/gd/api/calendar?id=${encodeURIComponent(id)}`;
    if (await attempt(pathUrl) || await attempt(qsUrl)) {
      if (window.fcApi?.removeById) {
        window.fcApi.removeById(id);
      } else {
        if (typeof window.refreshCalendar === "function") window.refreshCalendar();
      }
      return true;
    }
    throw new Error("Delete failed for event #" + id);
  }

  const tryJobDelete = async (jobId) => {
    const byPath = `/api/jobs/${jobId}`;
    const byQuery = `/api/jobs?id=${jobId}`;
    return (await attempt(byPath)) || (await attempt(byQuery));
  };

  const tryTaskDelete = async (taskId) => {
    const byPath = `/api/tasks/${taskId}`;
    const byQuery = `/api/tasks?id=${taskId}`;
    return (await attempt(byPath)) || (await attempt(byQuery));
  };

  if (isJob) {
    const num = isJob[1];
    if (await tryJobDelete(num)) {
      if (typeof window.refreshCalendar === "function") window.refreshCalendar();
      return true;
    }
    throw new Error("Delete failed for job " + num);
  }

  if (isTask) {
    const num = isTask[1];
    if (await tryTaskDelete(num)) {
      if (typeof window.refreshCalendar === "function") window.refreshCalendar();
      return true;
    }
    throw new Error("Delete failed for task " + num);
  }

  const uA = `/gd/api/calendar/${encodeURIComponent(id)}`;
  const uB = `/gd/api/calendar?id=${encodeURIComponent(id)}`;
  if (await attempt(uA) || await attempt(uB)) {
    if (typeof window.refreshCalendar === "function") window.refreshCalendar();
    return true;
  }
  throw new Error("Delete failed for id " + id);
}
catch (e) {
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
