
// gd universal delete helper (2025-10-17)
// - robust fallback for /api/jobs and /gd/api/calendar
// - handles 409 with confirm() and retries with ?force=1
// - tries both path-param and query-param variants
(function () {
  function qs(sel, ctx){ return (ctx||document).querySelector(sel); }
  function qsa(sel, ctx){ return Array.from((ctx||document).querySelectorAll(sel)); }

  async function doFetch(method, url){
    const res = await fetch(url, { method, headers: { "Accept": "application/json" } });
    let bodyText = await res.text().catch(()=>"" );
    let body = null;
    try { body = JSON.parse(bodyText); } catch(e){}
    return { ok: res.ok, status: res.status, body, text: bodyText };
  }

  function normalizeId(raw){
    // "job-10" -> {kind:"job", id:"10"}
    // "task-7" -> {kind:"task", id:"7"}
    // "15" -> {kind:"calendar", id:"15"}
    const m = String(raw).match(/^(job|task)-(\d+)$/i);
    if (m) return { kind: m[1].toLowerCase(), id: m[2] };
    return { kind: "calendar", id: String(raw) };
  }

  async function tryDeleteJob(id, opts={promptOnForce:true}){
    // Try variants in order
    // 1) DELETE /api/jobs/ID
    // 2) DELETE /api/jobs?id=ID
    // if 409 -> confirm -> add force=1 and retry both
    const variants = [
      `/api/jobs/${id}`,
      `/api/jobs?id=${encodeURIComponent(id)}`,
    ];
    // first pass without force
    for (const url of variants){
      const r = await doFetch("DELETE", url);
      if (r.ok) return {ok:true, status:r.status, urlTried:url};
      if (r.status === 409) {
        if (!opts.promptOnForce || window.confirm("Zakázku nelze smazat kvůli návaznostem. Chceš to smazat i tak (force)?")) {
          // retry with force=1 on both shapes
          const forceVariants = [
            url.includes("?") ? `${url}&force=1` : `${url}?force=1`,
            `/api/jobs/${id}?force=1`,
            `/api/jobs?id=${encodeURIComponent(id)}&force=1`,
          ];
          for (const fu of forceVariants){
            const fr = await doFetch("DELETE", fu);
            if (fr.ok) return {ok:true, status:fr.status, urlTried:fu};
          }
          return {ok:false, status:409};
        } else {
          return {ok:false, status:409, cancelled:true};
        }
      }
    }
    // If first pass gave 400 on both, try with force=1 as a fallback as well (defensive)
    for (const url of variants){
      const fu = url.includes("?") ? `${url}&force=1` : `${url}?force=1`;
      const fr = await doFetch("DELETE", fu);
      if (fr.ok) return {ok:true, status:fr.status, urlTried:fu};
    }
    return {ok:false, status:400};
  }

  async function tryDeleteTask(id){
    // Tasks were working via query param; still add fallback
    const variants = [
      `/api/tasks/${id}`,
      `/api/tasks?id=${encodeURIComponent(id)}`,
    ];
    for (const url of variants){
      const r = await doFetch("DELETE", url);
      if (r.ok) return {ok:true, status:r.status, urlTried:url};
    }
    return {ok:false};
  }

  async function tryDeleteCalendar(rawId){
    const {kind, id} = normalizeId(rawId);
    if (kind === "job") {
      return await tryDeleteJob(id);
    }
    if (kind === "task") {
      return await tryDeleteTask(id);
    }
    // calendar-only numeric id
    const r = await doFetch("DELETE", `/gd/api/calendar?id=${encodeURIComponent(id)}`);
    return {ok:r.ok, status:r.status};
  }

  async function refreshIf(fn){
    try{ await fn(); }catch(e){ console.error(e); }
    // Try to call page-local reloaders if present
    if (typeof window.reloadCalendar === "function") return window.reloadCalendar();
    if (typeof window.loadCalendar === "function") return window.loadCalendar();
    if (typeof window.loadJobs === "function") return window.loadJobs();
    if (typeof window.loadTasks === "function") return window.loadTasks();
    // Fallback
    try { location.reload(); } catch(e){}
  }

  // Bind auto handlers
  function bindButtons(){
    // Any button/link with [data-delete] attribute
    qsa("[data-delete]").forEach(btn=>{
      if (btn.__gdBound) return;
      btn.__gdBound = true;
      btn.addEventListener("click", async (e)=>{
        e.preventDefault();
        const target = btn.getAttribute("data-delete");
        if (!target) return;

        // Supported formats:
        //   jobs:10   -> delete job 10 (with force fallback)
        //   tasks:7   -> delete task 7
        //   cal:15    -> delete calendar row 15
        //   cal:job-10  or cal:task-7 -> mapped via normalizeId
        const [area, identRaw] = String(target).split(":");
        const ident = identRaw || "";
        let res = {ok:false};
        if (area === "jobs") {
          res = await tryDeleteJob(ident);
        } else if (area === "tasks") {
          res = await tryDeleteTask(ident);
        } else if (area === "cal") {
          res = await tryDeleteCalendar(ident);
        }

        if (!res.ok) {
          alert("Smazání se nepodařilo (HTTP "+(res.status||"")+")");
          return;
        }
        await refreshIf(async ()=>{});
      });
    });
  }

  // Expose helpers globally for older pages
  window.gdDelete = {
    job: tryDeleteJob,
    task: tryDeleteTask,
    calendar: tryDeleteCalendar,
    bind: bindButtons,
  };

  // Auto-bind once DOM is ready
  if (document.readyState === "loading"){
    document.addEventListener("DOMContentLoaded", bindButtons);
  } else {
    bindButtons();
  }
})();
