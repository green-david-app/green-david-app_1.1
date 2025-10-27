// === Calendar Hotfix 1.2 helper ===
(function(){
  function clampEventWidths(){
    document.querySelectorAll('.fc-daygrid-event')
      .forEach(function(el){
        el.style.maxWidth = '100%';
        el.style.width = '100%';
      });
  }
  function setMobileOptions(){
    if (window.innerWidth <= 680 && window.FullCalendar && window.gdCalendar && window.gdCalendar.setOption){
      try{
        window.gdCalendar.setOption('dayMaxEventRows', 3);
        window.gdCalendar.setOption('eventDisplay', 'block');
      }catch(e){}
    }
  }
  if (typeof ResizeObserver !== 'undefined'){
    new ResizeObserver(clampEventWidths).observe(document.documentElement);
  }
  document.addEventListener('DOMContentLoaded', function(){
    clampEventWidths(); setMobileOptions();
  });
  window.addEventListener('orientationchange', function(){
    setTimeout(function(){ clampEventWidths(); setMobileOptions(); }, 250);
  });
})();