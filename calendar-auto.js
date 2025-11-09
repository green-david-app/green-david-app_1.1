
// Standalone month/day renderer + actions for Open/Edit/Delete.
// Uses /gd/api/calendar?month=YYYY-MM and DELETE ...?id=ID endpoints.

(function(){
  const grid = document.getElementById('grid');
  const monthTitle = document.getElementById('monthTitle');
  const sheet = document.getElementById('sheet');
  const sheetDateEl = document.getElementById('sheetDate');
  const dayBox = document.getElementById('dayEventsBox');

  let focus = new Date(); // today

  function ymd(d){ return d.toISOString().slice(0,10); }
  function ymStr(d){ return d.toISOString().slice(0,7); } // YYYY-MM

  function addMonths(d, n){
    const x = new Date(d);
    x.setMonth(x.getMonth()+n);
    return x;
  }

  function humanMonth(d){
    const fmt = new Intl.DateTimeFormat('cs-CZ', {month:'long', year:'numeric'});
    let s = fmt.format(d);
    return s.charAt(0).toUpperCase()+s.slice(1);
  }

  function el(tag, cls, html){
    const e = document.createElement(tag);
    if(cls) e.className = cls;
    if(html!=null) e.innerHTML = html;
    return e;
  }

  async function fetchMonth(d){
    const url = `/gd/api/calendar?month=${ymStr(d)}`;
    const r = await fetch(url);
    if(!r.ok) throw new Error('Nepodařilo se načíst kalendář');
    return r.json();
  }

  function listFromApiDay(apiDay){
    // duck-typing: snažíme se vyčíst data z různých tvarů
    const date = apiDay.date || apiDay.day || apiDay.d || apiDay[0] || '';
    const items = apiDay.items || apiDay.events || apiDay.evts || apiDay[1] || [];
    return {date, items:(items||[]).map(normItem)};
  }

  function normItem(e){
    const id = e.id || e._id || e.id_str || e.key || '';
    const type = e.type || e.kind || e.category || 'other';
    const title = e.title || e.name || e.text || '';
    const start = e.start || e.date || '';
    return {id:String(id), type:String(type), title:String(title), start:String(start)};
  }

  function openSheet(dateStr){
    sheetDateEl.textContent = dateStr;
    sheet.style.display = 'block';
  }

  function closeSheet(){
    sheet.style.display = 'none';
  }

  function wireSheetClose(){
    sheet.addEventListener('click', (e)=>{
      if(e.target === sheet) closeSheet();
    });
    document.addEventListener('keydown', (e)=>{
      if(e.key === 'Escape') closeSheet();
    });
  }

  function fillDayList(day){
    const rows = day.items.map(it=>{
      return `
      <div class="row" data-ev-id="${it.id}" data-ev-type="${it.type}" data-ev-date="${day.date}">
        <div class="trow-title" data-title>${it.title}</div>
        <div class="row-actions">
          <button class="tact open" data-act="open">Otevřít</button>
          <button class="tact edit" data-act="edit">Upravit</button>
          <button class="tact del" data-act="del">Smazat</button>
        </div>
      </div>`;
    }).join('');
    dayBox.innerHTML = rows || '<div style="padding:16px;color:#777">Žádné položky</div>';
    // wire
    if(window.__wireDayList){ window.__wireDayList(); }
    else attachHandlers(dayBox);
  }

  function attachHandlers(root){
    // fallback handler when __wireDayList neexistuje
    root.addEventListener('click', function(ev){
      const btn = ev.target.closest('[data-act]');
      if(!btn) return;
      const row = btn.closest('.row');
      const idm = (row && (row.getAttribute('data-ev-id')||'')).match(/\d+$/);
      const id = idm ? idm[0] : '';
      const type = (row && row.getAttribute('data-ev-type')) || 'other';
      const date = (row && row.getAttribute('data-ev-date')) || '';
      const titleEl = row && (row.querySelector('[data-title]')||row.querySelector('.trow-title'));
      const title = titleEl ? (titleEl.textContent||'').trim() : '';

      if(btn.dataset.act==='del'){
        const url = (type==='job') ? '/gd/api/jobs?id='+id
                 : (type==='task'||type==='reminder') ? '/gd/api/tasks?id='+id
                 : '/gd/api/notes?id='+id;
        fetch(url, {method:'DELETE'}).then(r=>{
          if(r.ok){ loadMonth(); openDay(date); } else { alert('Smazání selhalo'); }
        }).catch(()=>alert('Smazání selhalo'));
        return;
      }

      if((btn.dataset.act==='open'||btn.dataset.act==='edit') && window.openQuickEditor){
        window.openQuickEditor({id, type, date, title});
      }
    }, {once:true}); // připne se znovu při dalším renderu
  }

  async function loadMonth(){
    const data = await fetchMonth(focus);
    const daysRaw = data.days || data || [];
    const days = daysRaw.map(listFromApiDay);

    grid.innerHTML = '';
    monthTitle.textContent = humanMonth(focus);

    // mřížka 6x7
    const first = new Date(focus.getFullYear(), focus.getMonth(), 1);
    const start = new Date(first);
    start.setDate(1 - ((first.getDay()+6)%7)); // Po=0

    const byDate = new Map(days.map(d=>[d.date, d]));

    for(let i=0;i<42;i++){
      const d = new Date(start); d.setDate(start.getDate()+i);
      const ds = d.toISOString().slice(0,10);
      const apiDay = byDate.get(ds) || {date: ds, items: []};
      const cell = el('div', 'day'+(d.getMonth()!==focus.getMonth()?' muted':''), '');
      cell.innerHTML = `<div class="num">${d.getDate()}</div>`;
      apiDay.items.slice(0,5).forEach(it=>{
        const pill = el('div','pill');
        pill.textContent = it.title || '';
        cell.appendChild(pill);
      });
      cell.addEventListener('click', ()=>{
        fillDayList(apiDay);
        openSheet(ds);
      });
      grid.appendChild(cell);
    }
  }

  function openDay(dateStr){
    fetchMonth(focus).then(data=>{
      const daysRaw = data.days || data || [];
      const day = (daysRaw.map(listFromApiDay).find(d=>d.date===dateStr)) || {date:dateStr, items:[]};
      fillDayList(day);
      openSheet(dateStr);
    }).catch(()=>{});
  }

  document.getElementById('prevBtn').addEventListener('click', ()=>{ focus = addMonths(focus,-1); loadMonth(); });
  document.getElementById('nextBtn').addEventListener('click', ()=>{ focus = addMonths(focus,+1); loadMonth(); });
  (function wireSheetClose(){
    sheet.addEventListener('click', (e)=>{ if(e.target === sheet) sheet.style.display='none'; });
    document.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') sheet.style.display='none'; });
  })();

  // start
  loadMonth().catch(err=>{
    console.error(err);
    monthTitle.textContent = 'Kalendář – nepodařilo se načíst data';
  });
})();
