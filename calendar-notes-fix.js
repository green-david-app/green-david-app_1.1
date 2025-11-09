
// Minimal, Safari-safe utilities + dekorace řádků v dayEventsBox
(function(){
  function onReady(fn){
    if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', fn); }
    else { fn(); }
  }

  // Později voláno z wireup.js při každém přerenderu:
  window.__decorateDayList = function(root){
    var box = root || document.getElementById('dayEventsBox') || document;
    if(!box) return;

    box.querySelectorAll('.row').forEach(function(row){
      if(row.querySelector('.row-actions')) return; // už má
      var titleEl = row.querySelector('[data-title]') || row.querySelector('.trow-title') || row.firstElementChild;
      if(!titleEl) return;

      var actions = document.createElement('div');
      actions.className = 'row-actions';
      function mk(label, cls, act){
        var b = document.createElement('button');
        b.className = 'tact '+cls;
        b.setAttribute('data-act', act);
        b.textContent = label;
        return b;
      }
      actions.appendChild(mk('Otevřít','open','open'));
      actions.appendChild(mk('Upravit','edit','edit'));
      actions.appendChild(mk('Smazat','del','del'));
      titleEl.insertAdjacentElement('afterend', actions);
    });
  };

  // Když se DOM změní, zkus dekorovat
  onReady(function(){
    var box = document.getElementById('dayEventsBox');
    if(!box) return;
    var mo = new MutationObserver(function(){ window.__decorateDayList(box); });
    mo.observe(box, {childList:true, subtree:true});
  });
})();
