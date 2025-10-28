
(function(){
  const grid = document.getElementById("calendarGrid");
  const monthLabel = document.getElementById("monthLabel");
  const prevBtn = document.getElementById("prevMonth");
  const nextBtn = document.getElementById("nextMonth");
  const addButtons = document.querySelectorAll(".btn.add");
  const modal = document.getElementById("eventModal");
  const evDate = document.getElementById("evDate");
  const evTitle = document.getElementById("evTitle");
  const evDetails = document.getElementById("evDetails");
  const evColor = document.getElementById("evColor");
  const evType = document.getElementById("evType");

  let current = new Date();
  current.setDate(1);

  function fmtMonth(d){
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
  }
  function fmtDate(d){
    return d.toISOString().slice(0,10);
  }

  async function load(){
    const ym = fmtMonth(current);
    monthLabel.textContent = new Intl.DateTimeFormat('cs-CZ', {month:'long', year:'numeric'}).format(current);
    const res = await fetch(`/gd/api/calendar?month=${ym}`);
    const data = await res.json();
    renderMonth(current, data.events || []);
  }

  const tzIso = (d)=>{
  const p = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  return p.toISOString().slice(0,10);
};
function openDaySheet(date, items){
  const sheet = document.getElementById('daySheet');
  const sDate = document.getElementById('sheetDate');
  const sBody = document.getElementById('sheetBody');
  if(!sheet) return;
  sDate.textContent = new Intl.DateTimeFormat('cs-CZ',{weekday:'long', day:'numeric', month:'long', year:'numeric'}).format(date);
  sBody.innerHTML = '';
  if(!items || items.length===0){
    const p = document.createElement('p'); p.textContent = 'Žádné záznamy'; sBody.appendChild(p);
  } else {
    items.forEach(ev=>{
      const row = document.createElement('div'); row.className='sheet-item';
      row.innerHTML = '<div class="swatch" style="background:'+ (ev.color||'#2e7d32') +'"></div>'
                    + '<div class="meta"><div class="t">'+(ev.title||ev.details||'(bez názvu)')+'</div>'
                    + (ev.details?'<div class="n">'+ev.details+'</div>':'') + '</div>';
      const del = document.createElement('button'); del.className='btn ghost'; del.textContent='Smazat';
      del.addEventListener('click', async ()=>{ if(confirm('Smazat záznam?')){ await fetch(`/gd/api/calendar/${ev.id}`, {method:'DELETE'}); sheet.close(); load(); } });
      row.appendChild(del);
      sBody.appendChild(row);
    });
  }
  sheet.showModal();
}
function renderMonth(firstDay, events){
    grid.innerHTML = "";
    const year = firstDay.getFullYear();
    const month = firstDay.getMonth();
    const firstWeekday = new Date(year, month, 1).getDay(); // 0=Sun
    const offset = (firstWeekday + 6) % 7; // make Monday first
    const daysInMonth = new Date(year, month+1, 0).getDate();
    const prevMonthDays = new Date(year, month, 0).getDate();

    const dates = [];
    for(let i=offset-1;i>=0;i--){
      dates.push({date:new Date(year, month-1, prevMonthDays - i), other:true});
    }
    for(let d=1; d<=daysInMonth; d++){
      dates.push({date:new Date(year, month, d), other:false});
    }
    const total = Math.ceil(dates.length/7)*7;
    for(let i=dates.length;i<total;i++){
      dates.push({date:new Date(year, month+1, i - dates.length + 1), other:true});
    }

    const byDay = {};
    for(const e of events){
      (byDay[e.date] ||= []).push(e);
    }

    dates.forEach(({date, other}) => {
      const cell = document.createElement('div');
      cell.className = 'day-cell ' + (other ? 'day-other' : '');
      const head = document.createElement('div');
      head.className = 'date';
      head.textContent = date.getDate() + '.';
      cell.appendChild(head);

      const list = document.createElement('div');
      (byDay[fmtDate(date)] || []).forEach(ev => {
        const item = document.createElement('div');
        item.className = 'event';
        item.style.background = ev.color || '#2e7d32';
        const span = document.createElement('span');
        span.className = 'title';
        span.textContent = ev.title;
        const del = document.createElement('button');
        del.className = 'del';
        del.textContent = '×';
        del.title = 'Smazat';
        del.addEventListener('click', async (e) => {
          e.stopPropagation();
          if(confirm('Opravdu smazat záznam?')){
            await fetch(`/gd/api/calendar/${ev.id}`, {method:'DELETE'});
            load();
          }
        });
        item.appendChild(span);
        item.appendChild(del);
        list.appendChild(item);
      });
      cell.appendChild(list);
      cell.addEventListener('click', ()=>{
        const k = tzIso(date);
        openDaySheet(date, byDay[k] || []);
      });
      cell.addEventListener('dblclick', ()=> openModal(fmtDate(date), 'note'));
      grid.appendChild(cell);
    });
  }

  prevBtn.addEventListener('click', ()=>{ current.setMonth(current.getMonth()-1); load(); });
  nextBtn.addEventListener('click', ()=>{ current.setMonth(current.getMonth()+1); load(); });
  addButtons.forEach(b=>{
    b.addEventListener('click', ()=>{
      openModal(new Date().toISOString().slice(0,10), b.dataset.type);
    })
  });

  function openModal(dateStr, type){
    evDate.value = dateStr;
    evType.value = type;
    // default colors per type
    evColor.value = type==='note' ? '#1976d2' : (type==='job' ? '#ef6c00' : '#2e7d32');
    evTitle.value = '';
    evDetails.value = '';
    modal.showModal();
  }

  document.getElementById('saveEvent').addEventListener('click', async (e)=>{
    e.preventDefault();
    const payload = {
      date: evDate.value,
      title: evTitle.value,
      details: evDetails.value,
      color: evColor.value,
      type: evType.value
    };
    const res = await fetch('/gd/api/calendar', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    if(res.ok){
      modal.close();
      load();
    } else {
      const t = await res.text();
      alert('Chyba: ' + t);
    }
  });

  load();
})();
