
(function(){
  function ready(fn){ if(document.readyState!=='loading'){ fn(); } else { document.addEventListener('DOMContentLoaded', fn); } }

  function ensureEditButtons(){
    try{
      // 1) Jobs list cards: add "Upravit" link next to actions
      document.querySelectorAll('.card .card-h + .card-c').forEach(function(cardC){
        const actionRow = cardC.querySelector('div[style*="display: flex"][style*="gap: 8px"]');
        if(!actionRow) return;
        if(actionRow._gd_has_edit) return;
        const openBtn = Array.from(actionRow.querySelectorAll('button')).find(b=>/Otevřít detail/i.test(b.textContent||""));
        const delBtn = Array.from(actionRow.querySelectorAll('button')).find(b=>/Smazat/i.test(b.textContent||""));
        // Heuristic: deduce ID from the surrounding card (the title span has onClick handler onOpen(z.id)).
        // We'll fall back to parsing the "Otevřít detail" button's onClick string if present in attribute, else skip.
        // Better approach: read from sibling KV date which doesn't have ID. So we parse from React key? Not accessible.
        // Practical approach: derive id via link we add using data-id attribute set by React? Not present. 
        // So we clone the "Otevřít detail" handler with a small shim to get the id on click.
        if(openBtn && !actionRow.querySelector('a.gd-edit-link')){
          // create the link and defer navigation to job_edit once we capture id via invoking open handler and intercept fetch
          const edit = document.createElement('a');
          edit.className = 'ghost gd-edit-link';
          edit.href = '#';
          edit.textContent = 'Upravit';
          edit.style.marginLeft = '4px';
          edit.onclick = function(ev){
            ev.preventDefault();
            // Try to infer job id from ancestor card title click handler argument.
            // Strategy: find the nearest .card, then find the title span with onClick.
            const card = ev.target.closest('.card');
            const titleSpan = card && card.querySelector('.card-h .linklike');
            if(titleSpan && titleSpan.onclick){
              // Temporarily wrap api to intercept the subsequent /api/jobs/<id> request
              const origFetch = window.fetch;
              let timer = null;
              window.fetch = function(url, opts){
                try{
                  const m = String(url).match(/\/api\/jobs\/(\d+)/);
                  if(m){
                    const id = m[1];
                    window.fetch = origFetch;
                    clearTimeout(timer);
                    location.href = '/job_edit.html?id='+id;
                    return Promise.reject(new Error('redirect_to_edit'));
                  }
                }catch(e){}
                return origFetch.apply(this, arguments);
              };
              // call original onclick to trigger loading detail (which will call /api/jobs/<id>)
              try{ titleSpan.onclick(); }catch(e){ window.fetch = origFetch; }
              // Fallback timeout
              timer = setTimeout(function(){ window.fetch = origFetch; alert('Nepodařilo se zjistit ID zakázky – otevři prosím detail a pak zkus znovu.'); }, 1200);
            } else {
              alert('Nejde zjistit ID ze seznamu – otevři prosím detail a klikni na „Upravit“ tam.');
            }
          };
          actionRow.appendChild(edit);
          actionRow._gd_has_edit = true;
        }
      });

      // 2) Job detail header: add "Upravit" link next to back button
      document.querySelectorAll('button.ghost').forEach(function(btn){
        if(/Zpět na seznam/i.test(btn.textContent||'') && !btn._gd_edit_added){
          // find job_id via the Export XLSX link nearby
          const container = btn.closest('.grid');
          const exportLink = container && container.querySelector('a[href*="/export/job_materials.xlsx?job_id="]');
          if(exportLink){
            const m = exportLink.getAttribute('href').match(/job_id=(\d+)/);
            if(m){
              const id = m[1];
              const edit = document.createElement('a');
              edit.className = 'ghost';
              edit.href = '/job_edit.html?id='+id;
              edit.textContent = 'Upravit';
              edit.style.marginLeft = '8px';
              btn.insertAdjacentElement('afterend', edit);
              btn._gd_edit_added = true;
            }
          }
        }
      });
    }catch(e){ /* silent */ }
  }

  ready(function(){
    ensureEditButtons();
    // Mutation observer to catch React re-renders
    const obs = new MutationObserver(function(){ ensureEditButtons(); });
    obs.observe(document.getElementById('app'), {childList:true, subtree:true});
  });
})();
