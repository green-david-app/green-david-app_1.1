function ReportsView(){
  const {useState,useEffect} = React;
  const [employees,setEmployees] = useState([]);
  const [employeeId,setEmployeeId] = useState("");
  const [from,setFrom] = useState(""); const [to,setTo] = useState("");
  const [rows,setRows] = useState([]); const [total,setTotal]=useState(0);
  React.useEffect(()=>{ (async()=>{ try{ const e = await api("/api/employees"); setEmployees(e.employees||[]);}catch(_){}})(); },[]);
  async function load(e){ e.preventDefault(); if(!employeeId) return; const q=new URLSearchParams({employee_id:employeeId, from:from||"", to:to||""}).toString(); const j=await api("/api/reports/employee_hours?"+q); setRows(j.rows||[]); setTotal(j.total_hours||0); }
  const exportHref = employeeId? ("/export/employee_hours.xlsx?"+new URLSearchParams({employee_id:employeeId, from:from||"", to:to||""}).toString()): "#";
  return (<div className="grid" style={{gridTemplateColumns:"1fr"}}>
    <div className="card">
      <div className="card-h"><div>Výkaz hodin zaměstnance</div></div>
      <div className="card-c">
        <form onSubmit={load}><div className="form-row">
          <select value={employeeId} onChange={e=>setEmployeeId(e.target.value)} required>
            <option value="">Vyber zaměstnance…</option>
            {employees.map(e=>(<option key={e.id} value={e.id}>{e.name}</option>))}
          </select>
          <input type="date" value={from} onChange={e=>setFrom(e.target.value)} placeholder="Od"/>
          <input type="date" value={to} onChange={e=>setTo(e.target.value)} placeholder="Do"/>
          <button type="submit">Načíst</button>
          <a className={"btn "+(employeeId?'':'disabled')} href={exportHref}>Export XLSX</a>
        </div></form>
        <div className="muted" style={{margin:"8px 0"}}>Celkem hodin: <b>{total}</b></div>
        <table className="table">
          <thead><tr><th>Datum</th><th>Hodiny</th><th>Zakázka</th><th>Kód</th><th>Místo</th><th>Popis</th></tr></thead>
          <tbody>{rows.map((r,i)=>(<tr key={i}><td>{r.date}</td><td>{r.hours}</td><td>{r.title}</td><td>{r.code}</td><td>{r.place||""}</td><td>{r.activity||""}</td></tr>))}</tbody>
        </table>
      </div>
    </div>
  </div>);
}
