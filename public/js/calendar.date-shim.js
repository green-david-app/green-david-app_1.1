
(function(){
  // best-effort shim: detect cells that look like days and annotate data-date via title attribute if present
  const guess = ()=>{
    const cells = document.querySelectorAll("#calendarGrid [data-date], #calendarGrid .day");
    // if any cell already has data-date, skip
    if ([...cells].some(c=>c.getAttribute("data-date"))) return;
    // try to use titles like "2025-11-28"
    document.querySelectorAll("#calendarGrid [title]").forEach(el=>{
      const t = el.getAttribute("title")||"";
      if (/^\d{4}-\d{2}-\d{2}$/.test(t)) el.setAttribute("data-date", t);
    });
  };
  window.addEventListener("DOMContentLoaded", ()=>{
    setTimeout(guess, 400);
    setTimeout(guess, 1200);
  });
})();
