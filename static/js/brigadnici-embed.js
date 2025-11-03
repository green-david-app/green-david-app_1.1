
(function(){
  function el(tag, attrs, html){
    const e = document.createElement(tag);
    if(attrs){ for(const [k,v] of Object.entries(attrs)) e.setAttribute(k, v); }
    if(html!=null) e.innerHTML = html;
    return e;
  }
  async function fetchJSON(url){ const r = await fetch(url,{credentials:'same-origin'}); if(!r.ok) throw new Error(await r.text()); return r.json(); }
  async function apiJSON(url, opt){ const r = await fetch(url, Object.assign({credentials:'same-origin', headers:{'Content-Type':'application/json'}}, opt||{})); if(!r.ok) throw new Error(await r.text()); return r.json(); }

  function inject(){
    const page = document.querySelector('.page-pad') || document.body;
    if(!page) return;
    if(document.getElementById('gd-emp-tabs')) return;

    const tabs = el('div', {id:'gd-emp-tabs', class:'tabs'}, `
      <button class="chip chip-on" id="gdTabEmp">Zaměstnanci</button>
      <button class="chip" id="gdTabBrig">Brigádníci</button>
    `);
    page.insertBefore(tabs, page.firstChild);

    const paneEmp = el('div', {id:'paneEmp'});
    const toMove = [];
    for(let i=1;i<page.children.length;i++){ toMove.push(page.children[i]); }
    toMove.forEach(ch => paneEmp.appendChild(ch));
    page.appendChild(paneEmp);

    const paneBrig = el('div', {id:'paneBrig', style:'display:none;'}, `
      <div class="card">
        <div class="card-header">Nový brigádník</div>
        <div class="card-body">
          <div class="form-row">
            <input id="bNewName" type="text" class="input" placeholder="Jméno" style="width: 280px;">
            <button id="bBtnAdd" class="btn btn-success" style="margin-left:8px;">Přidat</button>
          </div>
        </div>
      </div>
      <div class="card" style="margin-top: 12px;">
        <div class="card-header">Seznam</div>
        <div class="card-body">
          <div class="table">
            <table>
              <thead><tr><th style="width:60px">ID</th><th>Jméno</th><th>Role</th></tr></thead>
              <tbody id="bListBody"><tr><td colspan="3" class="muted">Načítám…</td></tr></tbody>
            </table>
          </div>
        </div>
      </div>
    `);
    page.appendChild(paneBrig);

    async function renderBrig(){
      try{
        const data = await fetchJSON('/api/employees');
        const rows = (data.employees||[]).filter(e => String(e.role||'').toLowerCase()==='brigádník');
        const tb = document.getElementById('bListBody');
        if(!tb) return;
        if(!rows.length){ tb.innerHTML='<tr><td colspan="3" class="muted">Žádní brigádníci</td></tr>'; return; }
        tb.innerHTML = rows.map(e => `<tr><td>${e.id}</td><td>${e.name||''}</td><td>${e.role||'brigádník'}</td></tr>`).join('');
      }catch(err){ const tb=document.getElementById('bListBody'); if(tb) tb.innerHTML='<tr><td colspan="3" class="muted">Chyba načítání</td></tr>'; }
    }

    function show(which){
      const isEmp = which==='emp';
      document.getElementById('gdTabEmp').classList.toggle('chip-on', isEmp);
      document.getElementById('gdTabBrig').classList.toggle('chip-on', !isEmp);
      paneEmp.style.display = isEmp ? '' : 'none';
      paneBrig.style.display = isEmp ? 'none' : '';
      if(!isEmp) renderBrig();
    }
    document.getElementById('gdTabEmp').addEventListener('click', ()=>show('emp'));
    document.getElementById('gdTabBrig').addEventListener('click', ()=>show('brig'));

    document.getElementById('bBtnAdd')?.addEventListener('click', async ()=>{
      const input = document.getElementById('bNewName');
      const name = (input.value||'').trim();
      if(!name) return;
      await apiJSON('/api/employees', { method:'POST', body: JSON.stringify({name, role:'brigádník'}) });
      input.value=''; renderBrig();
    });
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', inject);
  else inject();
})();
