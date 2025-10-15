
// iOS viewport fix
(function(){function setVh(){document.documentElement.style.setProperty('--vh',(window.innerHeight*0.01)+'px');}
setVh();window.addEventListener('resize',setVh,{passive:true});window.addEventListener('orientationchange',setVh);})();

// Calendar: tap day to expand (non-destructive)
(function(){
  function enhance(){
    const grid=document.querySelector('#calendarGrid, .calendar-grid, [data-calendar-grid]');
    if(!grid) return;
    Array.from(grid.children).forEach((cell)=>{
      if(cell.__enhanced) return; cell.__enhanced=true;
      cell.classList.add('gd-day');
      let panel=cell.querySelector('.gd-day-panel');
      if(!panel){
        panel=document.createElement('div'); panel.className='gd-day-panel';
        const ev=cell.querySelector('.gd-badges, .cal-evlist, .events, .badges');
        if(ev){ panel.appendChild(ev); } else { panel.innerHTML='<div class="empty small" style="opacity:.6">Žádné položky</div>'; }
        cell.appendChild(panel);
      }
      cell.addEventListener('click', function(e){
        if(e.target.closest('a,button,[data-href]')) return;
        cell.classList.toggle('open');
      });
      cell.querySelectorAll('[data-href]').forEach(el=>{
        if(el.__wired) return; el.__wired=true; el.style.cursor='pointer';
        el.addEventListener('click', function(ev){ ev.stopPropagation(); location.assign(el.dataset.href); });
      });
    });
  }
  if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',enhance);} else {enhance();}
  new MutationObserver(enhance).observe(document.body,{subtree:true,childList:true});
})();
