/* green-david calendar – add/delete fix + render (desktop + iPhone) */
(function () {
  const $ = (q, el = document) => el.querySelector(q);
  const $$ = (q, el = document) => Array.from(el.querySelectorAll(q));

  const state = {
    year: 0,
    month: 0, // 0..11
    items: [], // {id,type,date,text,color}
  };

  const monthNames = [
    "leden","únor","březen","duben","květen","červen",
    "červenec","srpen","září","říjen","listopad","prosinec"
  ];

  function toISO(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth()+1).padStart(2,"0");
    const day = String(d.getDate()).padStart(2,"0");
    return `${y}-${m}-${day}`;
  }

  function fromISO(s) {
    const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m) return null;
    return new Date(Number(m[1]), Number(m[2])-1, Number(m[3]));
  }

  async function api(path, opts={}) {
    const res = await fetch(path, {
      credentials: "same-origin",
      headers: {"Content-Type":"application/json"},
      ...opts
    });
    if (!res.ok) {
      let msg = res.statusText;
      try { const j = await res.json(); msg = j.error || msg; } catch {}
      throw new Error(msg);
    }
    try { return await res.json(); } catch { return {}; }
  }

  function showErr(msg) {
    const box = $("#js-error");
    if (!box) return alert(msg);
    box.textContent = msg || "Neznámá chyba";
    box.style.display = "block";
    setTimeout(()=> box.style.display="none", 3500);
  }

  function firstOfMonth(y, m) { return new Date(y, m, 1); }
  function lastOfMonth(y, m)  { return new Date(y, m+1, 0); }

  // --- Render ---------------------------------------------------------------
  function render() {
    const grid = $("#calendar");
    const {year, month} = state;

    $("#monthLabel").textContent = `${monthNames[month]} ${year}`;

    // build day cells (always 1..31 area but hide overflow days)
    const first = firstOfMonth(year, month);
    const last  = lastOfMonth(year, month);
    const daysInMonth = last.getDate();

    grid.innerHTML = "";
    for (let d = 1; d <= daysInMonth; d++) {
      const cell = document.createElement("div");
      cell.className = "day";
      const dateISO = `${year}-${String(month+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
      cell.dataset.date = dateISO;

      const head = document.createElement("div");
      head.className = "day-head";
      head.textContent = `${d}.`;
      cell.appendChild(head);

      const body = document.createElement("div");
      body.className = "day-body";
      cell.appendChild(body);

      grid.appendChild(cell);
    }

    // items → chips
    for (const it of state.items) {
      const cell = $(`.day[data-date="${it.date}"]`, grid);
      if (!cell) continue;
      const chip = document.createElement("div");
      chip.className = `chip ${it.type||"note"}`;
      chip.dataset.id = it.id;
      chip.title = it.text;

      const t = document.createElement("span");
      t.className = "chip-text";
      t.textContent = it.text;
      chip.appendChild(t);

      const x = document.createElement("button");
      x.className = "chip-close";
      x.type = "button";
      x.setAttribute("aria-label","Smazat");
      x.textContent = "×";
      chip.appendChild(x);

      $(".day-body", cell).appendChild(chip);
    }
  }

  // --- Load data ------------------------------------------------------------
  async function loadAndRender() {
    const from = toISO(firstOfMonth(state.year, state.month-1));
    const to   = toISO(lastOfMonth(state.year, state.month+1));
    const data = await api(`/gd/api/calendar?from=${from}&to=${to}`);
    // normalize coming payload into {id,type,date,text}
    const out = [];
    (data || []).forEach(x => {
      // backend vrací mix job-*, task-* atd.
      const id = x.id || x._id || x.uid;
      const date = x.date || x.day || x.when || x.d; // různé aliasy → snaž se
      const text = x.text || x.title || x.name || "";
      const type = x.type || (String(id||"").startsWith("job-") ? "job" :
                   String(id||"").startsWith("task-") ? "task" : "note");
      if (id && date) out.push({id, type, date, text});
    });
    state.items = out;
    render();
  }

  // --- Add / Delete ---------------------------------------------------------
  async function addItem(kind) {
    try {
      const date = prompt("Zadej datum (DD.MM.RRRR nebo RRRR-MM-DD):", toISO(new Date()).split("-").reverse().join("."));
      if (!date) return;
      const text = prompt(kind==="job" ? "Název zakázky:" : (kind==="task" ? "Text úkolu:" : "Text poznámky:"));
      if (!text) return;

      const iso = normalizeDate(date);
      await api("/gd/api/calendar", {
        method: "POST",
        body: JSON.stringify({ type: kind, date: iso, text })
      });
      await loadAndRender();
    } catch (e) { showErr(e.message); }
  }

  function normalizeDate(v) {
    // "15.10.2025" → "2025-10-15"
    const m = String(v).trim().match(/^(\d{1,2})[.\s-](\d{1,2})[.\s-](\d{4})$/);
    if (m) {
      const dd = m[1].padStart(2,"0");
      const mm = m[2].padStart(2,"0");
      return `${m[3]}-${mm}-${dd}`;
    }
    return v; // už ISO
  }

  async function deleteById(id) {
    if (!id) return;
    if (!confirm("Smazat položku?")) return;
    try {
      await api(`/gd/api/calendar?id=${encodeURIComponent(id)}`, { method: "DELETE" });
      await loadAndRender();               // ← po DELETE hned překreslit
    } catch (e) { showErr(e.message); }
  }

  // --- Events ---------------------------------------------------------------
  function bindEvents() {
    $("#prev").onclick = () => { if (--state.month < 0) { state.month = 11; state.year--; } loadAndRender(); };
    $("#next").onclick = () => { if (++state.month > 11) { state.month = 0;  state.year++; } loadAndRender(); };

    $("#btnAddNote").onclick = () => addItem("note");
    $("#btnAddTask").onclick = () => addItem("task");
    $("#btnAddJob").onclick  = () => addItem("job");

    // Tap/click do prázdného dne → rychlé přidání poznámky
    $("#calendar").addEventListener("click", (e) => {
      const cell = e.target.closest(".day");
      if (!cell) return;

      // klik na křížek?
      const closeBtn = e.target.closest(".chip-close");
      if (closeBtn) {
        const chip = closeBtn.closest(".chip");
        return deleteById(chip && chip.dataset.id);
      }

      // klik na chip – nic
      if (e.target.closest(".chip")) return;

      // klik do dne → rychlé přidání poznámky k tomuto dni
      const dateISO = cell.dataset.date;
      const text = prompt(`Poznámka pro ${dateISO}:`);
      if (!text) return;
      api("/gd/api/calendar", {
        method:"POST",
        body: JSON.stringify({ type:"note", date: dateISO, text })
      }).then(loadAndRender).catch(err => showErr(err.message));
    }, { passive: true });

    // iOS: podpora „tap“ (touchstart) na křížek
    $("#calendar").addEventListener("touchstart", (e) => {
      const closeBtn = e.target.closest(".chip-close");
      if (closeBtn) {
        e.preventDefault();
        const chip = closeBtn.closest(".chip");
        deleteById(chip && chip.dataset.id);
      }
    }, { passive: false });
  }

  // --- Init -----------------------------------------------------------------
  (function init() {
    const today = new Date();
    state.year = today.getFullYear();
    state.month = today.getMonth();
    bindEvents();
    loadAndRender().catch(e => showErr(e.message));
  })();
})();
