// === Calendar Mobile Fix 1.3 — JS helper ===
document.addEventListener('DOMContentLoaded', function() {
  (function ensureViewport(){
    var head=document.head||document.getElementsByTagName('head')[0]; if(!head) return;
    if(!document.querySelector('meta[name="viewport"]')){ var m=document.createElement('meta'); m.name='viewport'; m.content='width=device-width, initial-scale=1'; head.appendChild(m); }
  })();
  (function ensureResponsiveCss(){
    var head=document.head||document.getElementsByTagName('head')[0]; if(!head) return;
    var hasCss=[].slice.call(document.querySelectorAll('link[rel="stylesheet"]')).some(function(l){return(l.getAttribute('href')||'').indexOf('/static/css/responsive.css')!==-1;});
    if(!hasCss){ var link=document.createElement('link'); link.rel='stylesheet'; link.href='/static/css/responsive.css?v=1.3'; head.appendChild(link); }
  })();
  var el=document.getElementById('calendar')||document.querySelector('.calendar, .month-view');
  if(el && (!el.parentElement || !el.parentElement.classList.contains('calendar-wrapper'))){ var wrap=document.createElement('div'); wrap.className='calendar-wrapper'; el.parentNode.insertBefore(wrap, el); wrap.appendChild(el); }
  (function clamp(node){ while(node && node!==document.body){ node.style.overflowX='hidden'; node=node.parentElement; } })(el||document.body);
  try{
    var isMobile=window.matchMedia&&window.matchMedia('(max-width: 768px)').matches;
    var api=null; if(el && el.calendar) api=el.calendar; if(!api && window.gdCalendar) api=window.gdCalendar;
    if(api && typeof api.setOption==='function'){ api.setOption('height','auto'); api.setOption('contentHeight','auto'); api.setOption('handleWindowResize',true); if(isMobile){ try{api.setOption('dayMaxEventRows',2);}catch(e){} try{ if(api.view && api.view.type!=='listWeek') api.changeView('listWeek'); }catch(e){} } }
  }catch(e){}
});
