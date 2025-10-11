
window.GD_Timesheets = (function(){
  async function api(url,opts={}){const r=await fetch(url,Object.assign({headers:{"Content-Type":"application/json"}},opts));const j=await r.json().catch(()=>({}));if(!r.ok||j.ok===false)throw new Error((j&&(j.error||j.detail))||("HTTP "+r.status));return j}
  async function mount(root){
    root.innerHTML = `<div class="grid">
      <div class="card"><div class="card-h"><div>Výkaz hodin zaměstnance</div></div><div class="card-c">
        <form id="rep_form"><div class="form-row">
          <select id="rep_employee" required></select>
          <input type="date" id="rep_from"><input type="date" id="rep_to">
          <button type="submit">Načíst</button>
          <a id="rep_export" class="btn disabled" href="#">Export CSV</a>
        </div></form>
        <div class="muted" style="margin:8px 0">Celkem hodin: <b id="rep_total">0</b></div>
        <table class="table"><thead><tr><th>Datum</th><th>Hodiny</th><th>Zakázka</th><th>Kód</th><th>Město</th><th>Místo</th><th>Popis</th></tr></thead><tbody id="rep_tbody"></tbody></table>
      </div></div>
      <div class="card"><div class="card-h"><div>Přidat záznam do výkazu</div></div><div class="card-c">
        <div id="rep_msg" class="alert" style="display:none"></div>
        <form id="rep_add"><div class="form-row">
          <select id="ts_employee"></select><select id="ts_job"></select></div>
          <div class="form-row"><input type="date" id="ts_date" required><input type="number" id="ts_hours" step="0.25" min="0" placeholder="Hodiny" required></div>
          <div class="form-row"><input id="ts_place" placeholder="Místo (volit.)"><input id="ts_activity" placeholder="Popis (volit.)"></div>
          <div class="form-row"><button type="submit">Přidat do výkazu</button></div>
        </form>
      </div></div>
    </div>`;
    const employees=(await api("/api/employees")).employees||[]; const jobs=(await api("/api/jobs")).jobs||[];
    const empSel=root.querySelector("#rep_employee"); empSel.innerHTML=`<option value="">Vyber zaměstnance…</option>`+employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join("");
    root.querySelector("#ts_employee").innerHTML=employees.map(e=>`<option value="${e.id}">${e.name}</option>`).join("");
    root.querySelector("#ts_job").innerHTML=jobs.map(j=>`<option value="${j.id}">${j.title} (${j.code||""})</option>`).join("");

    const tbody=root.querySelector("#rep_tbody"), totalEl=root.querySelector("#rep_total"), exp=root.querySelector("#rep_export");
    async function loadRows(){
      const emp=empSel.value; if(!emp) return;
      const f=root.querySelector("#rep_from").value||"", t=root.querySelector("#rep_to").value||"";
      const j=await api(`/api/reports/employee_hours?employee_id=${emp}&from=${f}&to=${t}`);
      tbody.innerHTML=j.rows.map(r=>`<tr><td>${r.date}</td><td>${r.hours}</td><td>${r.title||""}</td><td>${r.code||""}</td><td>${r.city||""}</td><td>${r.place||""}</td><td>${r.activity||""}</td></tr>`).join("");
      totalEl.textContent=j.total_hours; exp.classList.remove("disabled"); exp.href=\`/export/employee_hours.csv?employee_id=\${emp}&from=\${f}&to=\${t}\`;
    }
    root.querySelector("#rep_form").onsubmit=(ev)=>{ev.preventDefault(); loadRows();};

    const msg=root.querySelector("#rep_msg");
    root.querySelector("#rep_add").onsubmit=async ev=>{
      ev.preventDefault(); msg.style.display="none";
      const d={employee_id:Number(root.querySelector("#ts_employee").value), job_id:Number(root.querySelector("#ts_job").value), date:root.querySelector("#ts_date").value, hours:Number(root.querySelector("#ts_hours").value), place:root.querySelector("#ts_place").value||null, activity:root.querySelector("#ts_activity").value||null};
      try{ await api("/api/timesheets",{method:"POST", body:JSON.stringify(d)}); msg.textContent="Zapsáno."; msg.className="alert ok"; msg.style.display="block"; await loadRows(); ev.target.reset(); }
      catch(ex){ msg.textContent="Uložení selhalo: "+ex.message; msg.className="alert error"; msg.style.display="block"; }
    };
  }
  return {mount};
})();