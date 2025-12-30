
(function(){
  // If arriving with hash like #d-YYYY-MM-DD try to scroll to that day cell after calendar renders
  function apply(){
    const hash = location.hash || "";
    if(!hash.startsWith("#d-")) return;
    const date = hash.slice(3);
    // find any element that carries data-date
    const cand = document.querySelector(`[data-date="${date}"]`);
    if (cand){
      cand.classList.add("day--highlight");
      cand.scrollIntoView({behavior:"smooth", block:"center"});
      setTimeout(()=>cand.classList.remove("day--highlight"), 3200);
    }
  }
  // observe for a bit as calendar renders asynchronously
  const obs = new MutationObserver(()=>apply());
  window.addEventListener('DOMContentLoaded', ()=>{
    apply();
    const grid = document.getElementById("calendarGrid");
    if(grid) obs.observe(grid, {childList:true, subtree:true});
    setTimeout(()=>obs.disconnect(), 6000);
  });
})();
