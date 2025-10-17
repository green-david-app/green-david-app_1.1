
const ui = (()=>{
  const q=(s,el=document)=>el.querySelector(s);
  const fmtDate=(d)=>new Date(d).toISOString().slice(0,10);

  async function getMe(){
    try{
      const r=await fetch('/api/me');
      const j=await r.json();
      q('#userName').textContent = (j && j.user && j.user.name) ? j.user.name : 'Admin';
    }catch(e){}
  }

  async function loadJobs(){
    const wrap=q('#jobsList'); if(!wrap) return;
    wrap.innerHTML='';
    const r=await fetch('/api/jobs'); const data=await r.json();
    (data.jobs||[]).forEach(job=>{
      const el=document.createElement('div'); el.className='card';
      el.innerHTML=`<div class="title">${job.name||'Bez názvu'}</div>
        <span class="badge">${job.status||'nová'}</span>
        <button class="btn danger">Smazat</button>`;
      el.querySelector('button').onclick=()=>deleteJob(job.id);
      wrap.appendChild(el);
    });
  }
  async function addJob(){
    const name=q('#jobTitle').value.trim();
    const status=q('#jobStatus').value;
    if(!name) return;
    await fetch('/api/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,status})});
    q('#jobTitle').value=''; await loadJobs();
  }
  async function deleteJob(id){
    const trueId=String(id).startsWith('job-')?String(id).split('job-').pop():id;
    await fetch(`/api/jobs?id=${encodeURIComponent(trueId)}`,{method:'DELETE'});
    await loadJobs();
  }

  async function loadTasks(){
    const list=q('#tasksList'); if(!list) return;
    list.innerHTML='';
    const r=await fetch('/api/tasks'); const data=await r.json();
    (data.tasks||[]).forEach(t=>{
      const el=document.createElement('div'); el.className='card';
      el.innerHTML=`<span class="badge">${t.status||'nový'}</span>
        <div class="title">${t.title||'(bez názvu)'}</div>
        ${t.due?`<span class="pill">${t.due}</span>`:''}
        <button class="btn danger">smazat</button>`;
      el.querySelector('button').onclick=()=>deleteTask(t.id);
      list.appendChild(el);
    });
  }
  async function populateTaskSelects(){
    const selA=q('#taskAssignee'), selJ=q('#taskJob');
    if(!selA||!selJ) return;
    const [re,rj]=await Promise.all([fetch('/api/employees'),fetch('/api/jobs')]);
    const employees=(await re.json()).employees||[];
    const jobs=(await rj.json()).jobs||[];
    selA.innerHTML='<option value=\"\">Bez přiřazení</option>'+employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join('');
    selJ.innerHTML='<option value=\"\">Bez zakázky</option>'+jobs.map(j=>`<option value="${j.id}">${j.name}</option>`).join('');
  }
  async function addTask(){
    const title=q('#taskTitle').value.trim();
    const due=q('#taskDue').value||null;
    const assignee=q('#taskAssignee').value||null;
    const job=q('#taskJob').value||null;
    if(!title) return;
    await fetch('/api/tasks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,due,assignee,job})});
    q('#taskTitle').value=''; q('#taskDue').value=''; await loadTasks();
  }
  async function deleteTask(id){
    const trueId = String(id).startsWith('task-')?String(id).split('task-').pop():id;
    await fetch(`/api/tasks?id=${encodeURIComponent(trueId)}`,{method:'DELETE'});
    await loadTasks();
  }

  async function loadCalendar(){
    const list=q('#calendarList'); if(!list) return;
    list.innerHTML='';
    const today=new Date();
    const from=new Date(today.getFullYear(),today.getMonth(),1);
    const to=new Date(today.getFullYear(),today.getMonth()+1,0);
    const r=await fetch(`/gd/api/calendar?from=${fmtDate(from)}&to=${fmtDate(to)}`);
    const data=await r.json();
    (data.events||[]).forEach(ev=>{
      const el=document.createElement('div'); el.className='card';
      el.innerHTML=`<div class="title">${ev.title||'Event'}</div>
        ${ev.date?`<span class="pill">${ev.date}</span>`:''}
        <button class="btn danger">Smazat</button>`;
      el.querySelector('button').onclick=()=>deleteCalendar(ev.id);
      list.appendChild(el);
    });
  }
  async function addCalendarEvent(){
    const title=q('#newEventTitle').value.trim();
    const date=q('#newEventDate').value;
    if(!title||!date) return;
    await fetch('/gd/api/calendar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,date})});
    q('#newEventTitle').value=''; q('#newEventDate').value=''; await loadCalendar();
  }
  async function deleteCalendar(id){
    const trueId=String(id).replace(/^job-/,'');
    await fetch(`/gd/api/calendar?id=${encodeURIComponent(trueId)}`,{method:'DELETE'});
    await loadCalendar();
  }

  async function loadEmployees(){
    const grid=q('#employeesList'); if(!grid) return;
    grid.innerHTML='';
    const r=await fetch('/api/employees'); const data=await r.json();
    (data.employees||[]).forEach(e=>{
      const card=document.createElement('div'); card.className='card'; card.style.flexDirection='column'; card.style.alignItems='flex-start';
      card.innerHTML=`<div class="title">${e.name}</div><div class="pill">ID ${e.id}</div>`;
      grid.appendChild(card);
    });
  }

  function boot(){
    getMe(); loadJobs(); loadTasks(); populateTaskSelects(); loadCalendar(); loadEmployees();
  }
  document.addEventListener('DOMContentLoaded', boot);
  return { addJob, addTask, addCalendarEvent };
})();
