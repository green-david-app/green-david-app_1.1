/* green-david calendar – add/delete fix (fallback JSON -> form) + iOS taps */
(function () {
  const $ = (q, el = document) => el.querySelector(q);

  const state = { year: 0, month: 0, items: [] };
  const monthNames = ["leden","únor","březen","duben","květen","červen","červenec","srpen","září","říjen","listopad","prosinec"];

  const toISO = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth()+1).padStart(2,"0");
    const day = String(d.getDate()).padStart(2,"0");
    return `${y}-${m}-${day}`;
  };
  const firstOfMonth = (y,m)=>new Date(y,m,1);
  const lastOfMonth  = (y,m)=>new Date(y,m+1,0);

  function showErr(msg){ const t=$("#js-error"); (t?t:alert).call(window, msg||"Chyba"); if(t){t.textContent=msg||"Chyba"; t.style.display="block"; setTimeout(()=>t.style.display="none",3000);} }

  async function apiGet(url){
    const r = await fetch(url, {credentials:"same-origin"});
    if(!r.ok) throw new Error(r.statusText);
    try { return await r.json(); } catch { return []; }
  }

  // --- POST helper: try JSON, on 400 retry x-www-form-urlencoded ------------
  async function postCalendar(payload) {
    // server čeká klíč "day" (ne "date") – pošleme oboje pro jistotu
    const bodyJson = { ...payload, day: payload.day || payload.date };
    let r = await fetch("/gd/api/calendar", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(bodyJson)
    });

    if (r.status === 400) {
      // fallback na form-url-encoded (některá nasazení to vyžadují)
      const form = new URLSearchParams();
      Object.entries(bodyJson).forEach(([k,v])=> v!=null && form.append(k, v));
      r = await fetch("/gd/api/calendar", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
        body: form.toString()
      });
    }

    if (!r.ok) {
      let msg = r.statusText;
      try { const j = await r.json(); msg = j.error || msg; } catch {}
      throw new Error(msg || "Nepodařilo se uložit položku");
    }
    return true;
  }

  function normalizeDate(v){
    const m=String(v).trim().match(/^(\d{1,2})[.\s-](\d{1,2})[.\s-](\d{4})$/);
    if(m){ return `${m[3]}-${m[2].padStart(2,"0")}-${m[1].padStart(2,"0")}`; }
    return v; // už ISO
  }

  // --- RENDER ---------------------------------------------------------------
  function render() {
    $("#monthLabel").textContent = `${monthNames[state.month]} ${state.year}`;
    const grid = $("#calendar");
    grid.innerHTML = "";

    const last = lastOfMonth(state.year, state.month).getDate();
    for (let d=1; d<=last; d++){
      const dateISO = `${state.year}-${String(state.month+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
      const cell = document.createElement("div"); cell.className="day"; cell.dataset.date=dateISO;
      cell.innerHTML = `<div class="day-head">${d}.</div><div class="day-body"></div>`;
      grid.appendChild(cell);
    }

    for (const it of state.items){
      const cell = grid.querySelector(`.day[data-date="${it.date}"]`); if(!cell) continue;
      const chip = document.createElement("div");
      chip.className = `chip ${it.type||"note"}`; chip.dataset.id = it.id; chip.title = it.text||"";
      chip.innerHTML = `<span class="chip-text"></span><button class="chip-close" type="button" aria-label="Smazat">×</button>`;
      chip.querySelector(".chip-text").textContent = it.text||"";
      cell.querySelector(".day-body").appendChild(chip);
    }
  }

  async function loadAndRender(){
    const from = toISO(firstOfMonth(state.year, state.month-1));
    const to   = toISO(lastOfMonth(state.year, state.month+1));
    const data = await apiGet(`/gd/api/calendar?from=${from}&to=${to}`);
    state.items = (data||[]).map(x=>{
      const id = x.id || x._id || x.uid;
      const date = x.date || x.day || x.when || x.d;
      const text = x.text || x.title || x.name || "";
      const type = x.type || (String(id).startsWith("job-") ? "job" : String(id).startsWith("task-") ? "task" : "note");
      return id && date ? {id, date, text, type} : null;
    }).filter(Boolean);
    render();
  }

  // --- ADD / DELETE ---------------------------------------------------------
  async function addItem(kind, dateISO) {
    try{
      const dateIn = dateISO || prompt("Datum (DD.MM.RRRR nebo RRRR-MM-DD):", toISO(new Date()));
      if(!dateIn) return;
      const text = prompt(kind==="job"?"Název zakázky:":kind==="task"?"Text úkolu:":"Text poznámky:");
      if(!text) return;
      const iso = normalizeDate(dateIn);
      await postCalendar({ type: kind, day: iso, date: iso, text });
      await loadAndRender();
    }catch(e){ showErr(e.message); }
  }

  async function deleteById(id){
    if(!id) return;
    if(!confirm("Smazat položku?")) return;
    try{
      const r = await fetch(`/gd/api/calendar?id=${encodeURIComponent(id)}`, {method:"DELETE", credentials:"same-origin"});
      if(!r.ok) throw new Error("Smazání se nezdařilo");
      await loadAndRender();
    }catch(e){ showErr(e.message); }
  }

  // --- EVENTS ---------------------------------------------------------------
  function bindEvents(){
    $("#prev").onclick = ()=>{ if(--state.month<0){state.month=11;state.year--;} loadAndRender(); };
    $("#next").onclick = ()=>{ if(++state.month>11){state.month=0; state.year++;} loadAndRender(); };

    $("#btnAddNote").onclick = ()=> addItem("note");
    $("#btnAddTask").onclick = ()=> addItem("task");
    $("#btnAddJob").onclick  = ()=> addItem("job");

    // click/tap do dne = rychlé přidání poznámky
    $("#calendar").addEventListener("click", (e)=>{
      const x = e.target.closest(".chip-close");
      if (x) { const chip = x.closest(".chip"); return deleteById(chip?.dataset.id); }

      const cell = e.target.closest(".day");
      if (!cell || e.target.closest(".chip")) return;
      addItem("note", cell.dataset.date);
    }, {passive:true});

    // iOS tap na křížek
    $("#calendar").addEventListener("touchstart",(e)=>{
      const x = e.target.closest(".chip-close");
      if (x){ e.preventDefault(); const chip = x.closest(".chip"); deleteById(chip?.dataset.id); }
    }, {passive:false});
  }

  // --- INIT -----------------------------------------------------------------
  (function init(){
    const t = new Date();
    state.year = t.getFullYear(); state.month = t.getMonth();
    bindEvents();
    loadAndRender().catch(e=>showErr(e.message));
  })();
})();
