
function fmt(d){const dt=(d instanceof Date)?d:new Date(d);const y=dt.getFullYear();const m=String(dt.getMonth()+1).padStart(2,'0');const day=String(dt.getDate()).padStart(2,'0');return `${y}-${m}-${day}`;}
async function jget(u){const r=await fetch(u,{headers:{'Accept':'application/json'}});return r.json()}
async function jpost(u,d){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});try{return await r.json()}catch{return {ok:false}}}
async function renderCalendar(root){
  root.innerHTML='<div class="card">Načítám kalendář…</div>';let summary=[];
  try{const resp=await jget('/api/calendar');if(!resp||!resp.ok)throw new Error('bad');summary=resp.summary||[]}catch(e){root.innerHTML='<div class="card">Kalendář: chyba načítání.</div>';return}
  const monthState={dt:new Date()};const byDate=Object.fromEntries(summary.map(x=>[x.date,x]));
  const header=document.createElement('div');header.className='cal-head';
  const title=document.createElement('div');title.textContent='Kalendář';
  const ctrl=document.createElement('div');ctrl.className='cal-ctrl';
  const prev=document.createElement('button');prev.textContent='◀';
  const next=document.createElement('button');next.textContent='▶';
  const lab=document.createElement('span');lab.className='mute';
  ctrl.append(prev,lab,next);header.append(title,ctrl);
  const grid=document.createElement('div');grid.className='cal-grid';
  const wrap=document.createElement('div');wrap.className='card';wrap.append(header,grid);
  root.innerHTML='';root.append(wrap);
  function rebuild(){grid.innerHTML='';const y=monthState.dt.getFullYear(),m=monthState.dt.getMonth();
    lab.textContent=monthState.dt.toLocaleDateString('cs-CZ',{month:'long',year:'numeric'});
    const first=new Date(y,m,1);const startDay=(first.getDay()+6)%7;const daysInMonth=new Date(y,m+1,0).getDate();
    for(let i=0;i<startDay;i++){const d=document.createElement('div');d.className='day mute';grid.append(d)}
    for(let d=1;d<=daysInMonth;d++){const div=document.createElement('div');div.className='day';
      const ds=`${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
      const dn=document.createElement('div');dn.className='dnum';dn.textContent=d;div.append(dn);
      const badges=document.createElement('div');badges.className='badges';div.append(badges);
      const sum=byDate[ds];if(sum){const bz=document.createElement('span');bz.className='badge';bz.textContent=`Z: ${sum.jobs}`;badges.append(bz);
        const bv=document.createElement('span');bv.className='badge';bv.textContent=`V: ${sum.work_logs}`;badges.append(bv)}
      else{const b0=document.createElement('span');b0.className='badge';b0.textContent='—';badges.append(b0)}
      const items=document.createElement('div');items.className='items';div.append(items);
      div.addEventListener('click',async()=>{items.innerHTML='<span class="mute">Načítám detail…</span>';
        try{const detail=await jget(`/api/calendar?date=${ds}`);const data=(detail&&detail.data)||{jobs:[],work_logs:[]};
          items.innerHTML='';data.jobs.forEach(j=>{const it=document.createElement('div');it.className='item';it.textContent=j.title||j.name||'(bez názvu)';items.append(it)});
          if(!data.jobs||data.jobs.length===0){const it=document.createElement('div');it.className='item mute';it.textContent='Žádné zakázky.';items.append(it)}
          if(data.work_logs&&data.work_logs.length){const it=document.createElement('div');it.className='item';it.textContent=`+ ${data.work_logs.length} výkazů`;items.append(it)}}
        catch(e){items.innerHTML='<span class="mute">Detail se nepodařilo načíst.</span>'}});
      grid.append(div)}}prev.onclick=()=>{monthState.dt=new Date(monthState.dt.getFullYear(),monthState.dt.getMonth()-1,1);rebuild()};
  next.onclick=()=>{monthState.dt=new Date(monthState.dt.getFullYear(),monthState.dt.getMonth()+1,1);rebuild()};rebuild()}
async function renderWorklogs(root){
  root.innerHTML='<div class="card">Načítám výkazy…</div>';
  const card=document.createElement('div');card.className='card';const h=document.createElement('h2');h.textContent='Výkazy';card.append(h);
  const form=document.createElement('form');form.className='worklog';form.innerHTML=`
    <input name="employee_name" placeholder="Zaměstnanec (např. Adam)" required>
    <input name="work_date" type="date" required>
    <input name="hours" type="number" step="0.25" min="0" placeholder="Hodiny" required>
    <input name="job_title" placeholder="Zakázka (název)" required>
    <input name="note" placeholder="Poznámka">
    <button type="submit">Přidat výkaz</button>`;card.append(form);
  const tableWrap=document.createElement('div');tableWrap.className='grid';card.append(tableWrap);
  root.innerHTML='';root.append(card);
  async function loadTable(){tableWrap.innerHTML='<div class="center">Načítám…</div>';
    try{const resp=await jget('/api/worklogs');const logs=(resp&&resp.work_logs)||[];
      if(!logs.length){tableWrap.innerHTML='<div class="center">Zatím žádné výkazy.</div>';return}
      const tbl=document.createElement('table');tbl.className='logs';
      tbl.innerHTML='<thead><tr><th>Datum</th><th>Zaměstnanec</th><th>Zakázka</th><th>Hodiny</th><th>Pozn.</th></tr></thead>';
      const tb=document.createElement('tbody');logs.forEach(w=>{const tr=document.createElement('tr');
        tr.innerHTML=`<td>${w.work_date||''}</td><td>${w.employee_name||''}</td><td>${w.job_title||''}</td><td>${w.hours||''}</td><td>${w.note||''}</td>`;tb.append(tr)});
      tbl.append(tb);tableWrap.innerHTML='';tableWrap.append(tbl)}catch(e){tableWrap.innerHTML='<div class="center">Chyba načítání výkazů.</div>'}}
  form.addEventListener('submit',async ev=>{ev.preventDefault();const fd=new FormData(form);const payload=Object.fromEntries(fd.entries());payload.hours=parseFloat(payload.hours||'0');await jpost('/api/worklogs',payload);await loadTable();form.reset()});
  await loadTable()}
