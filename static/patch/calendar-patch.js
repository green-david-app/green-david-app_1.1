
// calendar refresh + delete glue (2025-10-17)
(function(){
  async function reload(){
    if (typeof window.loadCalendar === "function") return window.loadCalendar();
    // fallback: trigger re-fetch used by legacy pages
    const e = document.querySelector("[data-cal-reload]");
    if (e) e.click();
  }
  window.reloadCalendar = reload;

  // Enhance legacy delete buttons if present
  document.addEventListener("click", function(e){
    const a = e.target.closest("[data-cal-delete-id]");
    if (!a) return;
    e.preventDefault();
    const raw = a.getAttribute("data-cal-delete-id");
    window.gdDelete.calendar(raw).then(r=>{
      if (!r.ok){ alert("Smazání kalendáře selhalo"); return; }
      reload();
    });
  }, true);
})();
