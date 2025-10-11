
window.GD_Calendar=(function(){
  const pad=n=>String(n).padStart(2,'0');
  const iso=d=>d.toISOString().slice(0,10);
  function monthFromTo(y,m){let y2=y,m2=m+1;if(m2>12){y2++;m2=1}return [`${y}-${pad(m)}-01`,`${y2}-${pad(m2)}-01`];}
  async function jfetch(u,o={}){const r=await fetch(u,Object.assign({headers:{'Content-Type':'application/json'}},o));const j=await r.json().catch(()=>({}));if(!r.ok||j.ok===false)throw new Error((j&&(j.error||j.detail))||('HTTP '+r.status));return j}
  function draw(root,ym,events){
    const grid=root.querySelector('#cal_grid'), title=root.querySelector('#cal_title'), sel=root.querySelector('#sel_date');
    grid.innerHTML=''; title.textContent=`${ym.y}-${pad(ym.m)}`;
    const first=new Date(ym.y,ym.m-1,1), start=new Date(first); const wd=d=>(d===0?7:d); start.setDate(1-(wd(first.getDay())-1));
    ['Po','Út','St','Čt','Pá','So','Ne'].forEach(d=>{const h=document.createElement('div');h.className='cal-dow';h.textContent=d;grid.appendChild(h);});
    const days=Array.from({length:42},(_,i)=>new Date(start.getFullYear(),start.getMonth(),start.getDate()+i)); const today=iso(new Date());
    days.forEach(d=>{const k=iso(d), inM=(d.getMonth()+1)===ym.m; const c=document.createElement('div'); c.className='cal-cell'+(inM?'':' dim')+(k===today?' today':''); c.dataset.date=k;
      const de=document.createElement('div');de.className='cal-date';de.textContent=d.getDate(); const dots=document.createElement('div');dots.className='cal-dots';
      const ev=events.filter(e=>e.start===k); ev.slice(0,4).forEach(e=>{const s=document.createElement('span'); s.className='dot '+(e.type||'note'); dots.appendChild(s);});
      if(ev.length>4){const m=document.createElement('span');m.className='dot more';m.textContent='+'+(ev.length-4);dots.appendChild(m);}
      c.appendChild(de); c.appendChild(dots); grid.appendChild(c);
    });
    grid.querySelectorAll('.cal-cell').forEach(c=>{c.onclick=()=>{const date=c.dataset.date; sel.textContent=date; root.querySelector('#f_date').value=date; renderList(root,events.filter(e=>e.start===date));};});
    const firstDay=`${ym.y}-${pad(ym.m)}-01`; sel.textContent=firstDay; root.querySelector('#f_date').value=firstDay; renderList(root,events.filter(e=>e.start===firstDay));
  }
  function renderList(root,evs){
    const ul=root.querySelector('#cal_list'); if(!evs.length){ul.innerHTML='<div class="muted">Žádné položky.</div>'; return;}
    ul.innerHTML=evs.map(e=>`<li><span class="pill ${(e.type||'note')}">${e.type||'note'}</span> ${e.title||''} <span style="opacity:.6">(${e.start})</span> <button class="tab" data-del="${e.id}">Smazat</button></li>`).join('');
    ul.querySelectorAll('button[data-del]').forEach(b=>{b.onclick=async()=>{try{await jfetch('/gd/api/calendar',{method:'DELETE',body:JSON.stringify({id:Number(b.dataset.del)})}); root.dispatchEvent(new CustomEvent('gd-reload'));}catch(ex){alert('Smazání selhalo: '+ex.message)}}});
  }
  async function mount(root){
    root.innerHTML=`
    <div class="grid two">
      <div class="card"><div class="card-h"><button class="tab" id="cal_prev">◀</button><b id="cal_title"></b><button class="tab" id="cal_next">▶</button></div>
        <div class="card-c"><div id="cal_grid" class="cal-grid"></div></div></div>
      <div class="card"><div class="card-h">Detail dne</div><div class="card-c">
        <div style="margin-bottom:8px"><b id="sel_date">Vyber den</b></div>
        <div id="cal_err" class="alert error" style="display:none"></div>
        <ul id="cal_list" class="list"></ul>
        <form id="cal_form">
          <div class="form-row">
            <select id="f_type"><option value="note">Poznámka</option><option value="task">Úkol</option><option value="job">Zakázka</option></select>
            <input type="date" id="f_date" required>
          </div>
          <div class="form-row"><input id="f_title" placeholder="Nadpis" required></div>
          <div class="form-row"><input id="f_notes" placeholder="Poznámka (volit.)"></div>
          <div class="form-row" id="f_job_more" style="display:none"><input id="f_client" placeholder="Klient"><input id="f_city" placeholder="Město"><input id="f_code" placeholder="Kód"></div>
          <div class="form-row" id="f_task_more" style="display:none"><input id="f_employee_id" placeholder="ID zaměstnance (volit.)"><input id="f_job_id" placeholder="ID zakázky (volit.)"></div>
          <div class="form-row"><button type="submit">Přidat</button></div>
        </form>
      </div></div>
    </div>`;
    const state={y:new Date().getFullYear(),m:new Date().getMonth()+1,events:[]}; const err=root.querySelector('#cal_err');
    async function load(){try{const [frm,to]=monthFromTo(state.y,state.m); const d=await jfetch(`/gd/api/calendar?from=${frm}&to=${to}`); state.events=d.events||[]; draw(root,{y:state.y,m:state.m},state.events);}catch(ex){err.textContent='Načtení selhalo: '+ex.message; err.style.display='block';}}
    root.querySelector('#cal_prev').onclick=()=>{state.m--; if(state.m<1){state.m=12;state.y--;} load();};
    root.querySelector('#cal_next').onclick=()=>{state.m++; if(state.m>12){state.m=1;state.y++;} load();};
    root.addEventListener('gd-reload', load);
    const typeSel=root.querySelector('#f_type'), jobMore=root.querySelector('#f_job_more'), taskMore=root.querySelector('#f_task_more');
    const toggle=()=>{jobMore.style.display=(typeSel.value==='job')?'flex':'none'; taskMore.style.display=(typeSel.value!=='note')?'flex':'none';}; typeSel.onchange=toggle; toggle();
    root.querySelector('#cal_form').onsubmit=async ev=>{ev.preventDefault(); err.style.display='none'; const p={type:typeSel.value,title:root.querySelector('#f_title').value.trim(),start:root.querySelector('#f_date').value,notes:(root.querySelector('#f_notes').value||'').trim()||null};
      if(!p.title||!p.start){err.textContent='Vyplň název a datum.'; err.style.display='block'; return;}
      if(p.type==='job'){p.client=root.querySelector('#f_client').value.trim(); p.city=root.querySelector('#f_city').value.trim(); p.code=root.querySelector('#f_code').value.trim(); if(!(p.client&&p.city&&p.code)){err.textContent='Pro zakázku vyplň Klient, Město a Kód.'; err.style.display='block'; return;}}
      if(p.type==='task'){const eid=root.querySelector('#f_employee_id').value.trim(), jid=root.querySelector('#f_job_id').value.trim(); if(eid)p.employee_id=Number(eid); if(jid)p.job_id=Number(jid);}
      try{await jfetch('/gd/api/calendar',{method:'POST',body:JSON.stringify(p)}); root.querySelector('#f_title').value=''; root.querySelector('#f_notes').value=''; await load();}
      catch(ex){err.textContent='Uložení selhalo: '+ex.message; err.style.display='block';}
    };
    await load();
  }
  return {mount};
})();