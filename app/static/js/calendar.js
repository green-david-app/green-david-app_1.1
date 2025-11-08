
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
  const saveBtn = document.getElementById("saveEvent");

  const API_BASE = "/gd/api/calendar";

  let current = new Date();
  current.setDate(1);
  let editingId = null;

  function fmtMonthLabel(d){
    const fmt = new Intl.DateTimeFormat('cs-CZ', {month:'long', year:'numeric'});
    return fmt.format(d);
  }

  function isoDate(d){
    const z = n => String(n).padStart(2,'0');
    return `${d.getFullYear()}-${z(d.getMonth()+1)}-${z(d.getDate())}`;
  }

  function startOfMonth(d){
    const x = new Date(d);
    x.setDate(1);
    x.setHours(0,0,0,0);
    return x;
  }
  function endOfMonth(d){
    const x = new Date(d);
    x.setMonth(x.getMonth()+1);
    x.setDate(0);
    x.setHours(0,0,0,0);
    return x;
  }

  function daysGridForMonth(d){
    const first = startOfMonth(d);
    const last = endOfMonth(d);
    const start = new Date(first);
    start.setDate(first.getDate() - ((first.getDay()+6)%7)); // Monday=0
    const end = new Date(last);
    end.setDate(last.getDate() + (6 - ((last.getDay()+6)%7)));
    const days = [];
    const cur = new Date(start);
    while(cur <= end){
      days.push(new Date(cur));
      cur.setDate(cur.getDate()+1);
    }
    return days;
  }

  async function load(){
    monthLabel.textContent = fmtMonthLabel(current);
    grid.innerHTML = "";
    const from = isoDate(startOfMonth(current));
    const to = isoDate(endOfMonth(current));
    const res = await fetch(`${API_BASE}?from=${from}&to=${to}`);
    if(!res.ok){
      const t = await res.text();
      alert('Chyba při načítání: ' + t);
      return;
    }
    const data = await res.json();
    const events = (data.events || data.items || []).map(e => ({
      id: e.id,
      date: e.date,
      title: e.title,
      type: e.type || "note",
      color: e.color || "#2e7d32",
      details: e.details || ""
    }));
    const days = daysGridForMonth(current);
    const byDate = {};
    for(const e of events){
      byDate[e.date] = byDate[e.date] || [];
      byDate[e.date].push(e);
    }
    const curMonth = current.getMonth();

    for(const day of days){
      const cell = document.createElement('div');
      cell.className = 'day-cell' + (day.getMonth() === curMonth ? '' : ' day-other');
      const key = isoDate(day);
      cell.dataset.date = key;

      const head = document.createElement('div');
      head.className = 'date';
      head.textContent = day.getDate();
      cell.appendChild(head);

      const list = document.createElement('div');
      list.className = 'events';
      (byDate[key] || []).forEach(ev => {
        const row = document.createElement('div');
        row.className = 'event';
        row.style.background = ev.color;
        row.title = ev.details || '';

        const span = document.createElement('div');
        span.className = 'title';
        span.textContent = ev.title;

        const actions = document.createElement('div');
        actions.className = 'actions';

        const editBtn = document.createElement('button');
        editBtn.className = 'del'; // reuse minimal style
        editBtn.textContent = '✎';
        editBtn.title = 'Upravit';
        editBtn.addEventListener('click', (eClick) => {
          eClick.stopPropagation();
          openEdit(ev);
        });

        const delBtn = document.createElement('button');
        delBtn.className = 'del';
        delBtn.textContent = '×';
        delBtn.title = 'Smazat';
        delBtn.addEventListener('click', async (eClick) => {
          eClick.stopPropagation();
          if(confirm('Opravdu smazat položku?')){
            const res = await fetch(`${API_BASE}/${ev.id}`, {method:'DELETE'});
            if(res.ok){ load(); } else { alert('Smazání selhalo'); }
          }
        });

        actions.appendChild(editBtn);
        actions.appendChild(delBtn);

        row.appendChild(span);
        row.appendChild(actions);

        list.appendChild(row);
      });

      cell.appendChild(list);

      cell.addEventListener('click', () => {
        editingId = null;
        evDate.value = key;
        evTitle.value = '';
        evDetails.value = '';
        evColor.value = '#2e7d32';
        evType.value = 'note';
        modal.showModal();
      });

      grid.appendChild(cell);
    }
  }

  function openEdit(ev){
    editingId = ev.id;
    evDate.value = ev.date;
    evTitle.value = ev.title;
    evDetails.value = ev.details || '';
    evColor.value = ev.color || '#2e7d32';
    evType.value = ev.type || 'note';
    modal.showModal();
  }

  prevBtn.addEventListener('click', () => {
    current.setMonth(current.getMonth()-1);
    load();
  });
  nextBtn.addEventListener('click', () => {
    current.setMonth(current.getMonth()+1);
    load();
  });

  addButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      editingId = null;
      evType.value = btn.dataset.type || 'note';
      const today = new Date();
      evDate.value = isoDate(today);
      evTitle.value = '';
      evDetails.value = '';
      evColor.value = evType.value === 'task' ? '#2e7d32' : (evType.value === 'job' ? '#ef6c00' : '#1976d2');
      modal.showModal();
    });
  });

  saveBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    const payload = {
      date: evDate.value,
      title: evTitle.value.trim(),
      type: evType.value,
      color: evColor.value,
      details: evDetails.value.trim()
    };
    if(!payload.title){
      alert("Zadejte název.");
      return;
    }
    let url = API_BASE;
    let method = 'POST';
    if(editingId){
      url = `${API_BASE}/${editingId}`;
      method = 'PUT';
    }
    const res = await fetch(url, {
      method,
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
