function CalendarView(){
  const {useState,useEffect,useMemo} = React;
  const today = new Date();
  const [ym, setYm] = useState({y: today.getFullYear(), m: today.getMonth()+1});
  const [events,setEvents] = useState([]);
  const [selDate,setSelDate] = useState(null);
  const ymKey = ym.y+"-"+String(ym.m).padStart(2,'0');
  function endOfMonth(y,m){ return new Date(y, m, 0).getDate(); }
  async function load(){
    const from = ymKey+"-01";
    const to = ymKey+"-"+String(endOfMonth(ym.y, ym.m)).padStart(2,'0');
    const j = await api(`/api/calendar?from=${from}&to=${to}`);
    setEvents(j.events||[]);
  }
  React.useEffect(()=>{ load().catch(()=>{}); }, [ymKey]);
  function addDays(d,i){ const dd=new Date(d); dd.setDate(dd.getDate()+i); return dd; }
  function iso(d){ return d.toISOString().slice(0,10); }
  function prev(){ let {y,m}=ym; m--; if(m<1){m=12;y--;} setYm({y,m}); }
  function next(){ let {y,m}=ym; m++; if(m>12){m=1;y++;} setYm({y,m}); }
  const first = new Date(ym.y, ym.m-1, 1);
  const start = new Date(first); start.setDate(1 - (first.getDay()||7) + 1); // Monday-based grid
  const days = Array.from({length:42}, (_,i)=> addDays(start,i));
  const map = useMemo(()=>{ const m = {}; for(const e of events){ const k = e.start; (m[k]=m[k]||[]).push(e); } return m; }, [events]);
  async function create(e){
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target).entries());
    const payload = {type:f.type,title:f.title,start:f.date,notes:f.notes};
    if(f.type==='task'){ payload.employee_id = f.employee_id? Number(f.employee_id): undefined; payload.job_id = f.job_id? Number(f.job_id): undefined; }
    if(f.type==='job'){ payload.client=f.client; payload.city=f.city; payload.code=f.code; }
    await api("/api/calendar",{method:"POST",body:JSON.stringify(payload)});
    e.target.reset(); await load(); alert("Uloženo");
  }
  const [employees,setEmployees] = useState([]);
  const [jobs,setJobs] = useState([]);
  React.useEffect(()=>{ (async()=>{ try{ const [e,j]=await Promise.all([api("/api/employees"), api("/api/jobs")]); setEmployees(e.employees||[]); setJobs(j.jobs||[]);}catch(_){} })(); },[]);
  return (<div className="grid" style={{gridTemplateColumns:"1.2fr 0.8fr"}}>
    <div className="card"><div className="card-h"><div>Kalendář</div><div className="right"><button className="ghost" onClick={prev}>◀</button><span style={{margin:"0 8px"}}>{ym.y}-{String(ym.m).padStart(2,'0')}</span><button className="ghost" onClick={next}>▶</button></div></div>
    <div className="card-c">
      <div className="cal-grid">
        {["Po","Út","St","Čt","Pá","So","Ne"].map(d=>(<div key={d} className="cal-dow">{d}</div>))}
        {days.map(d=>{
          const k=iso(d); const ev=(map[k]||[]);
          const inMonth = (d.getMonth()+1)===ym.m;
          return (<div key={k} className={"cal-cell"+(inMonth?"":" cal-dim")+(k===iso(new Date())?" cal-today":"")} onClick={()=>setSelDate(k)}>
            <div className="cal-date">{d.getDate()}</div>
            <div className="cal-dots">{ev.slice(0,4).map(e=>(<span key={e.id} title={e.title} className={"dot dot-"+e.type}></span>))}{ev.length>4?(<span className="dot more">+{ev.length-4}</span>):null}</div>
          </div>);
        })}
      </div>
    </div></div>
    <div className="card"><div className="card-h"><div>Detail dne</div></div>
      <div className="card-c">
        <div style={{marginBottom:8}}><b>{selDate||"Vyber den"}</b></div>
        <ul className="list">{(map[selDate]||[]).map(e=>(<li key={e.id}><span className={"pill "+e.type}>{e.type}</span> {e.title}</li>))}</ul>
        <form onSubmit={create}>
          <div className="form-row">
            <select name="type" defaultValue="note">
              <option value="note">Poznámka</option>
              <option value="task">Úkol</option>
              <option value="job">Zakázka</option>
            </select>
            <input type="date" name="date" defaultValue={selDate||ymKey+"-01"} required/>
          </div>
          <div className="form-row"><input name="title" placeholder="Nadpis" required/></div>
          <div className="form-row"><input name="notes" placeholder="Poznámka (volitelné)"/></div>
          <div className="form-row">
            <select name="employee_id" defaultValue=""><option value="">Zaměstnanec (volit.)</option>{employees.map(e=>(<option key={e.id} value={e.id}>{e.name}</option>))}</select>
            <select name="job_id" defaultValue=""><option value="">Zakázka (volit.)</option>{jobs.map(j=>(<option key={j.id} value={j.id}>{j.title} ({j.code})</option>))}</select>
          </div>
          <div className="form-row">
            <input name="client" placeholder="Klient (při zakázce)" />
            <input name="city" placeholder="Město (při zakázce)" />
            <input name="code" placeholder="Kód (při zakázce)" />
          </div>
          <div className="form-row"><button type="submit">Přidat</button></div>
        </form>
      </div>
    </div>
  </div>);
}
