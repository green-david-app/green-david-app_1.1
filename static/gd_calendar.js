
window.GD_Calendar = (function(){
  const pad=n=>String(n).padStart(2,"0"), iso=d=>d.toISOString().slice(0,10), eom=(y,m)=>new Date(y,m,0).getDate();
  async function api(url,opts={}){const r=await fetch(url,Object.assign({headers:{"Content-Type":"application/json"}},opts));const j=await r.json().catch(()=>({}));if(!r.ok||j.ok===false)throw new Error((j&&(j.error||j.detail))||("HTTP "+r.status));return j}
  async function mount(root){
    root.innerHTML = `<div class="grid two">
      <div class="card"><div class="card-h"><button class="tab" id="cal_prev">◀</button><b id="cal_title"></b><button class="tab" id="cal_next">▶</button></div>
        <div class="card-c"><div class="cal-grid" id="cal_grid"></div></div></div>
      <div class="card"><div class="card-h">Detail dne</div><div class="card-c">
        <div style="margin-bottom:8px"><b id="sel_date">Vyber den</b></div>
        <div id="cal_err" class="alert error" style="display:none"></div>
        <ul class="list" id="cal_list"></ul>
        <form id="cal_form">
          <div class="form-row">
            <select id="f_type"><option value="note">Poznámka</option><option value="task">Úkol</option><option value="job">Zakázka</option></select>
            <input type="date" id="f_date" required>
          </div>
          <div class="form-row"><input id="f_title" placeholder="Nadpis" required></div>
          <div class="form-row"><input id="f_notes" placeholder="Poznámka (volit.)"></div>
          <div class="form-row" id="f_job_more" style="display:none"><input id="f_client" placeholder="Klient"><input id="f_city" placeholder="Město"><input id="f_code" placeholder="Kód"></div>
          <div class="form-row" id="f_task_more" style="display:none"><input id="f_employee_id" placeholder="ID zaměstnance"><input id="f_job_id" placeholder="ID zakázky"></div>
          <div class="form-row"><button type="submit">Přidat</button></div>
        </form>
      </div></div>`;

    let today=new Date(); let ym={y:today.getFullYear(), m:today.getMonth()+1}; let selected=null;
    const grid=root.querySelector("#cal_grid"), title=root.querySelector("#cal_title"), sel=root.querySelector("#sel_date"), list=root.querySelector("#cal_list"), err=root.querySelector("#cal_err");

    const load = async ()=>{err.style.display="none"; const from=`${ym.y}-${pad(ym.m)}-01`, to=`${ym.y}-${pad(eom(ym.y,ym.m))}`; const j=await api(`/api/calendar?from=${from}&to=${to}`); draw(j.events||[])};
    function draw(events){
      const first=new Date(ym.y, ym.m-1, 1); const start=new Date(first); const dow=first.getDay()||7; start.setDate(1-(dow-1));
      const days=Array.from({length:42},(_,i)=>new Date(start.getFullYear(),start.getMonth(),start.getDate()+i));
      title.textContent=`${ym.y}-${pad(ym.m)}`;
      grid.innerHTML=["Po","Út","St","Čt","Pá","So","Ne"].map(d=>`<div class="cal-dow">${d}</div>`).join("")+
        days.map(d=>{const k=iso(d); const ev=events.filter(e=>e.start===k); const inMonth=(d.getMonth()+1)===ym.m;
          const dots=ev.slice(0,4).map(e=>`<span class="dot ${e.type}"></span>`).join("");
          const more=ev.length>4?`<span class="dot more">+${ev.length-4}</span>`:""; const todayIso=iso(new Date());
          return `<div class="cal-cell${inMonth?"":" dim"}${k===todayIso?" today":""}" data-date="${k}"><div class="cal-date">${d.getDate()}</div><div class="cal-dots">${dots}${more}</div></div>`;}).join("");
      Array.from(root.querySelectorAll(".cal-cell")).forEach(c=>{c.onclick=()=>{selected=c.getAttribute("data-date"); sel.textContent=selected; root.querySelector("#f_date").value=selected; renderList(events.filter(e=>e.start===selected));}});
      if(!selected){selected=`${ym.y}-${pad(ym.m)}-01`; sel.textContent=selected; root.querySelector("#f_date").value=selected; renderList(events.filter(e=>e.start===selected));}
    }
    function renderList(evts){list.innerHTML=evts.map(e=>`<li><span class="pill ${e.type}">${e.type}</span> ${e.title||""}</li>`).join("") || `<div class="muted">Žádné položky.</div>`}
    root.querySelector("#cal_prev").onclick=()=>{ym.m--; if(ym.m<1){ym.m=12; ym.y--;} load();};
    root.querySelector("#cal_next").onclick=()=>{ym.m++; if(ym.m>12){ym.m=1; ym.y++;} load();};

    const typeSel=root.querySelector("#f_type"), jobMore=root.querySelector("#f_job_more"), taskMore=root.querySelector("#f_task_more");
    const toggle=()=>{jobMore.style.display=(typeSel.value==="job")?"flex":"none"; taskMore.style.display=(typeSel.value!=="note")?"flex":"none"}; typeSel.onchange=toggle; toggle();

    root.querySelector("#cal_form").onsubmit=async ev=>{
      ev.preventDefault(); err.style.display="none";
      const type=typeSel.value; const payload={type, title:root.querySelector("#f_title").value.trim(), start:root.querySelector("#f_date").value, notes:(root.querySelector("#f_notes").value||"").trim()||null};
      if(!payload.title||!payload.start){err.textContent="Vyplň název a datum."; err.style.display="block"; return;}
      if(type==="job"){payload.client=root.querySelector("#f_client").value.trim(); payload.city=root.querySelector("#f_city").value.trim(); payload.code=root.querySelector("#f_code").value.trim();
        if(!(payload.client&&payload.city&&payload.code)){err.textContent="Pro zakázku vyplň Klient, Město a Kód."; err.style.display="block"; return;}}
      if(type==="task"){const eid=root.querySelector("#f_employee_id").value, jid=root.querySelector("#f_job_id").value; if(eid) payload.employee_id=Number(eid); if(jid) payload.job_id=Number(jid);}
      try{ await fetch("/api/calendar",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}).then(r=>r.json()); root.querySelector("#f_title").value=""; root.querySelector("#f_notes").value=""; await load(); }
      catch(ex){ err.textContent="Chyba uložení: "+ex.message; err.style.display="block"; }
    };
    await load();
  }
  return {mount};
})();