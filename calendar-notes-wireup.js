
// Jednotné ovládání open/edit/delete – používá ?id= na API
(function(){
  function normId(idStr){
    var m = (String(idStr||'').match(/\d+$/)||[])[0];
    return m || '';
  }
  function getRowInfo(row){
    var id = row && (row.getAttribute('data-ev-id') || row.getAttribute('data-id') || row.id || '');
    var type = (row && (row.getAttribute('data-ev-type') || row.dataset.type)) || 'other';
    id = normId(id);
    return {id:id, type:type};
  }
  function delByType(type, id){
    var url = (type==='job') ? '/gd/api/jobs?id='+id
            : (type==='task'||type==='reminder') ? '/gd/api/tasks?id='+id
            : '/gd/api/notes?id='+id;
    return fetch(url, {method:'DELETE'});
  }

  function handleClick(ev){
    var btn = ev.target.closest('[data-act]');
    if(!btn) return;
    var row = btn.closest('.row');
    var info = getRowInfo(row);
    if(!info.id){ alert('Chybí ID položky'); return; }

    if(btn.dataset.act==='del'){
      delByType(info.type, info.id).then(function(r){
        if(r && r.ok){ if(window.openSheet) openSheet(state.focusDate); if(window.load) load(); }
        else { alert('Smazání selhalo'); }
      }, function(){ alert('Smazání selhalo'); });
      ev.stopPropagation();
      return;
    }
    if(btn.dataset.act==='open' || btn.dataset.act==='edit'){
      if(window.openQuickEditor){
        var titleEl = row && (row.querySelector('[data-title]') || row.querySelector('.trow-title'));
        window.openQuickEditor({
          id: info.id,
          type: info.type,
          date: row && (row.getAttribute('data-ev-date') || row.dataset.date || ''),
          title: titleEl ? (titleEl.textContent||'').trim() : ''
        });
      }
      ev.stopPropagation();
    }
  }

  // Voláno po každém renderu denního seznamu
  window.__wireDayList = function(){
    var box = document.getElementById('dayEventsBox') || document;
    if(!box.__wired){
      box.addEventListener('click', handleClick);
      box.__wired = true;
    }
    if(window.__decorateDayList) window.__decorateDayList(box);
  };
})();
