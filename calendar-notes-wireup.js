
/* calendar-notes-wireup.js
 * Drop-in script to make notes save real text (not just label "Poznámka")
 * and to enable inline edit & delete for notes in the day list.
 *
 * It assumes the page already loads calendar data and renders a "Poznámka" tab
 * with a single textarea/input for note text and a "Uložit" button.
 * This script:
 *  - intercepts save -> sends POST /gd/api/tasks with {title, description, status, due_date}
 *  - renders note text in the list
 *  - adds Edit/Delete actions (PATCH /gd/api/tasks, DELETE /gd/api/tasks?id=...)
 */

(function () {
  const API = {
    createTask(noteText, dateISO) {
      // Make a title from the text (up to 40 chars)
      const title = (noteText || "").trim().substring(0, 40) || "Poznámka";
      const body = {
        // server expects at least title; we also send description
        title: title,
        description: noteText || "",
        status: "open",
        // due_date in YYYY-MM-DD if server supports it (calendar context supplies dateISO)
        due_date: dateISO || undefined
      };
      return fetch("/gd/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then(r => {
        if (!r.ok) throw new Error("POST /gd/api/tasks failed");
        return r.json().catch(() => ({}));
      });
    },
    patchTask(id, fields) {
      return fetch("/gd/api/tasks", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(Object.assign({ id }, fields)),
      }).then(r => {
        if (!r.ok) throw new Error("PATCH /gd/api/tasks failed");
        return r.json().catch(() => ({}));
      });
    },
    deleteTask(id) {
      return fetch(`/gd/api/tasks?id=${encodeURIComponent(id)}`, {
        method: "DELETE",
      }).then(r => {
        if (!r.ok) throw new Error("DELETE /gd/api/tasks failed");
        return r.json().catch(() => ({}));
      });
    },
    loadMonth(monthIso) {
      return fetch(`/gd/api/calendar?month=${encodeURIComponent(monthIso)}`)
        .then(r => r.json());
    }
  };

  // Helpers
  function findActiveDateISO() {
    // looks for a DOM element that stores current date; fallback to today
    const holder = document.querySelector("[data-current-date]");
    if (holder && holder.getAttribute("data-current-date")) {
      return holder.getAttribute("data-current-date");
    }
    // Try to read from visible center label "Den: DD.MM.YYYY"
    const dayLabel = Array.from(document.querySelectorAll("*"))
      .find(el => /\bDen:\s*\d{2}\.\d{2}\.\d{4}\b/.test(el.textContent || ""));
    if (dayLabel) {
      const m = dayLabel.textContent.match(/(\d{2})\.(\d{2})\.(\d{4})/);
      if (m) {
        const [_, d, mo, y] = m;
        return `${y}-${mo}-${d}`;
      }
    }
    // fallback
    const now = new Date();
    const pad = n => String(n).padStart(2, "0");
    return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
  }

  function flash(msg, ok=true) {
    let bar = document.getElementById("note-flash");
    if (!bar) {
      bar = document.createElement("div");
      bar.id = "note-flash";
      bar.style.position = "fixed";
      bar.style.bottom = "16px";
      bar.style.left = "50%";
      bar.style.transform = "translateX(-50%)";
      bar.style.padding = "10px 14px";
      bar.style.borderRadius = "12px";
      bar.style.background = ok ? "#1f7a4c" : "#a61b1b";
      bar.style.color = "white";
      bar.style.fontSize = "14px";
      bar.style.boxShadow = "0 4px 16px rgba(0,0,0,.25)";
      document.body.appendChild(bar);
    }
    bar.textContent = msg;
    bar.style.background = ok ? "#1f7a4c" : "#a61b1b";
    bar.style.opacity = "1";
    setTimeout(() => { bar.style.transition = "opacity .6s"; bar.style.opacity="0"; }, 1700);
  }

  // wire save for "Poznámka" tab
  function wireSave() {
    // try to locate notes tab container by its label
    const tabBtn = Array.from(document.querySelectorAll("button,div"))
      .find(el => (el.textContent || "").trim().toLowerCase() === "poznámka");
    // find the input under the notes tab pane (placeholder has "Text poznámky" in screenshots)
    const input = Array.from(document.querySelectorAll("textarea,input"))
      .find(el => (el.placeholder || "").toLowerCase().includes("poznámky"));
    const saveBtn = Array.from(document.querySelectorAll("button"))
      .find(el => (el.textContent || "").trim().toLowerCase() === "uložit");
    if (!input || !saveBtn) return;

    // prevent multiple bindings
    if (saveBtn.__notesWired) return;
    saveBtn.__notesWired = true;

    saveBtn.addEventListener("click", async (e) => {
      // Heuristic: active tab is "Poznámka" if its button has active style or notes input visible
      const isNotes = input.offsetParent !== null; 
      if (!isNotes) return; // do not hijack for other tabs

      e.preventDefault();
      const text = (input.value || "").trim();
      if (!text) { flash("Zadej text poznámky.", false); return; }
      const dateISO = findActiveDateISO();
      try {
        await API.createTask(text, dateISO);
        input.value = "";
        flash("Poznámka uložena.");
        // refresh UI list if present
        updateRenderedList();
      } catch (err) {
        console.error(err);
        flash("Uložení selhalo.", false);
      }
    });
  }

  // add edit/delete to rendered list (event delegation)
  function wireListActions() {
    const list = document.querySelector("[data-day-list]") || document.querySelector(".day-list, .items, .list");
    if (!list || list.__notesListWired) return;
    list.__notesListWired = true;

    list.addEventListener("click", async (e) => {
      const btn = e.target.closest("[data-edit-note],[data-delete-note]");
      if (!btn) return;
      const row = btn.closest("[data-task-id]");
      if (!row) return;
      const id = row.getAttribute("data-task-id");
      if (!id) return;

      if (btn.hasAttribute("data-delete-note")) {
        if (!confirm("Smazat položku?")) return;
        try {
          await API.deleteTask(id);
          row.remove();
          flash("Smazáno.");
        } catch (err) {
          console.error(err);
          flash("Smazání selhalo.", false);
        }
      } else if (btn.hasAttribute("data-edit-note")) {
        const textSpan = row.querySelector("[data-note-text]");
        const current = (textSpan?.textContent || "").trim();
        const next = prompt("Upravit poznámku:", current);
        if (next == null) return;
        try {
          await API.patchTask(id, { description: next, title: (next||"").substring(0,40)||"Poznámka" });
          if (textSpan) textSpan.textContent = next;
          flash("Upraveno.");
        } catch (err) {
          console.error(err);
          flash("Úprava selhala.", false);
        }
      }
    });
  }

  function updateRenderedList() {
    // try to refetch the day and re-render if app provides a function; otherwise minimally append
    // We ping month endpoint to make server refresh, then simulate user clicking on selected day to trigger app's own redraw.
    const selectedDay = document.querySelector("[data-day].selected, .calendar-day.selected, .day.selected");
    if (selectedDay) selectedDay.click();
    enhanceExistingRows();
  }

  function enhanceExistingRows() {
    // For each list row that is a note/task with title "Poznámka" but has description, append the text
    const rows = document.querySelectorAll("[data-day-list] [data-task-id], .day-list [data-task-id]");
    rows.forEach(row => {
      if (row.__enhanced) return;
      row.__enhanced = true;
      const title = (row.querySelector("[data-title]")?.textContent || row.textContent || "").trim().toLowerCase();
      // create container
      let textHolder = row.querySelector("[data-note-text]");
      if (!textHolder) {
        textHolder = document.createElement("span");
        textHolder.setAttribute("data-note-text","");
        textHolder.style.display = "block";
        textHolder.style.fontWeight = "500";
        textHolder.style.marginTop = "2px";
        row.appendChild(textHolder);
      }
      // If app stores description as data attribute, use it; fallback to title text
      const desc = row.getAttribute("data-description") || row.getAttribute("data-desc") || "";
      if (desc) textHolder.textContent = desc;

      // actions
      let actions = row.querySelector(".note-actions");
      if (!actions) {
        actions = document.createElement("span");
        actions.className = "note-actions";
        actions.style.float = "right";
        actions.style.gap = "8px";
        actions.style.display = "inline-flex";
        actions.innerHTML = `<button type="button" data-edit-note title="Upravit" aria-label="Upravit" style="border:none;background:transparent;cursor:pointer">✏️</button>
                             <button type="button" data-delete-note title="Smazat" aria-label="Smazat" style="border:none;background:transparent;cursor:pointer">✖️</button>`;
        row.appendChild(actions);
      }
    });
  }

  function boot() {
    wireSave();
    wireListActions();
    enhanceExistingRows();
    // observe DOM changes to re-apply
    const obs = new MutationObserver(() => {
      wireSave();
      wireListActions();
      enhanceExistingRows();
    });
    obs.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
