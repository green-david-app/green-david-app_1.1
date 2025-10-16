/* === GDA hotfix: Calendar interactions (add & delete) === */
(function(){
  const $ = (sel,root=document)=>root.querySelector(sel);
  const $$ = (sel,root=document)=>Array.from(root.querySelectorAll(sel));

  async function api(path, opts={}){
    const res = await fetch(path, {
      credentials:'same-origin',
      headers:{'Content-Type':'application/json'},
      ...opts
    });
    if(!res.ok){
      let t; try{ t = await res.text(); }catch{}
      throw new Error(t || res.statusText);
    }
    try{ return await res.json(); }catch{ return {}; }
  }

  // Mřížka kalendáře
  const grid = $('.calendar-grid') || $('#calendar-grid') || document;
  if(!grid) return;

  // U iOS bereme i touchstart, aby tap fungoval 100 %
  const on = (el,ev,fn)=>el.addEventListener(ev,fn,{passive:true});
  ['click','touchstart'].forEach(ev=>{
    on(grid, ev, (e)=>{
      // MAZÁNÍ: klik na křížek
      const delBtn = e.target.closest('[data-del], .event .close');
      if(delBtn){
        const id = delBtn.dataset.del || delBtn.getAttribute('data-id') || delBtn.dataset.id;
        if(!id) return;
        if(!confirm('Smazat položku v kalendáři?')) return;
        api(`/gd/api/calendar?id=${encodeURIComponent(id)}`, {method:'DELETE'})
          .then(()=> refresh())
          .catch((err)=> alert('Mazání selhalo: ' + err.message));
        e.stopPropagation();
        return;
      }

      // PŘIDÁNÍ: klepnutí do prázdného dne (mimo existující event)
      const day = e.target.closest('.day');
      if(day && !e.target.closest('.event')){
        const datum = day.dataset.date;
        if(!datum) return;
        const txt = prompt(`Text položky pro ${datum} (Zruš = nic nepřidat):`);
        if(!txt) return;
        const typ = prompt('Typ: z = Zakázka, u = Úkol, p = Poznámka', 'p')||'p';
        const typeMap = { 'z':'job', 'u':'task', 'p':'note' };
        const payload = { date: datum, type: typeMap[typ.toLowerCase()]||'note', text: txt.trim() };
        api('/gd/api/calendar', {method:'POST', body: JSON.stringify(payload)})
          .then(()=> refresh())
          .catch((err)=> alert('Vkládání selhalo: ' + err.message));
      }
    });
  });

  // Po změně znovu načti aktuální rozsah měsíce
  async function refresh(){
    try{
      const rangeFrom = document.body.dataset.rangeFrom || ( $('[data-range-from]') && $('[data-range-from]').dataset.rangeFrom );
      const rangeTo   = document.body.dataset.rangeTo   || ( $('[data-range-to]')   && $('[data-range-to]').dataset.rangeTo );
      if(!rangeFrom || !rangeTo){ location.reload(); return; }

      const data = await api(`/gd/api/calendar?from=${encodeURIComponent(rangeFrom)}&to=${encodeURIComponent(rangeTo)}`);
      // smaž staré čipy a vyrob znovu
      $$('.day .event').forEach(n=>n.remove());
      (data.items || data || []).forEach(addEventChip);
    }catch{
      location.reload();
    }
  }

  function addEventChip(it){
    const cell = document.querySelector(`.day[data-date="${it.date}"]`);
    if(!cell) return;
    const el = document.createElement('div');
    el.className = 'event ' + (it.color||'');
    el.innerHTML = `
      <span class="label">${escapeHtml(it.text||it.title||'')}</span>
      <button class="close" data-del="${it.id||it._id||''}" aria-label="Smazat">×</button>
    `;
    cell.appendChild(el);
  }

  function escapeHtml(s){
    return String(s).replace(/[&<>"']/g, m=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[m]));
  }
})();
