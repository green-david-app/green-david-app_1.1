// gd-mobile-hotfix: calendar behavior and iOS viewport corrections
(function(){
  function setVh(){
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', vh + 'px');
  }
  setVh();
  window.addEventListener('resize', setVh, {passive:true});
  window.addEventListener('orientationchange', setVh);

  function findGrid(){
    return document.querySelector('[data-calendar-grid]')
        || document.querySelector('.gd-calendar-grid')
        || document.querySelector('#calendar-grid')
        || document.querySelector('.calendar-grid');
  }

  function ensureWrap(grid){
    if(!grid) return;
    if(!grid.closest('.gd-calendar-wrap')){
      const wrap = document.createElement('div');
      wrap.className = 'gd-calendar-wrap gd-scroll';
      grid.parentNode.insertBefore(wrap, grid);
      wrap.appendChild(grid);
    }
  }

  function wireClicks(root){
    root.querySelectorAll('.gd-event, [data-event], [data-href]').forEach(function(el){
      if(el.__wired) return;
      el.__wired = true;
      el.style.cursor = 'pointer';
      el.addEventListener('click', function(e){
        const href = el.dataset.href || (el.querySelector('a[href]') && el.querySelector('a[href]').getAttribute('href'));
        if(href){
          window.location.assign(href);
        }
      }, false);
    });
  }

  function peelOverlays(){
    document.querySelectorAll('.overlay, .backdrop, .modal').forEach(function(el){
      const rect = el.getBoundingClientRect();
      const cs = getComputedStyle(el);
      const isHidden = (el.offsetParent === null) || (rect.width < 5 && rect.height < 5) || cs.visibility === 'hidden' || cs.opacity === '0';
      if(isHidden){
        el.style.pointerEvents = 'none';
      }
    });
  }

  document.addEventListener('DOMContentLoaded', function(){
    const grid = findGrid();
    ensureWrap(grid);
    if(grid){
      grid.classList.add('gd-calendar-grid');
      grid.querySelectorAll(':scope > *').forEach((d)=>d.classList.add('gd-day'));
    }
    wireClicks(document);
    peelOverlays();
  });

  const mo = new MutationObserver(function(){
    const grid = findGrid();
    ensureWrap(grid);
    if(grid) grid.classList.add('gd-calendar-grid');
    wireClicks(document);
    peelOverlays();
  });
  mo.observe(document.documentElement, {subtree:true, childList:true});

})();
