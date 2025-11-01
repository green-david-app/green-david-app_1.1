\
// timesheets_enhance.js
(function(){
  function qsa(s, root){return Array.from((root||document).querySelectorAll(s))}
  function parseCZDate(s){
    const m = String(s||'').trim().match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
    if(!m) return null;
    const d = new Date(Number(m[3]), Number(m[2])-1, Number(m[1]));
    if(isNaN(+d)) return null;
    d.setHours(0,0,0,0);
    return d;
  }
  function weekKey(d){
    const tmp = new Date(d);
    tmp.setDate(tmp.getDate() + 3 - ((tmp.getDay()+6)%7));
    const week1 = new Date(tmp.getFullYear(),0,4);
    const w = 1 + Math.round(((tmp.getTime() - week1.getTime())/86400000 - 3 + ((week1.getDay()+6)%7))/7);
    return `${tmp.getFullYear()}-W${String(w).padStart(2,'0')}`;
  }
  function fmtWeekLabel(key){
    const m = key.match(/^(\d{4})-W(\d{2})$/); if(!m) return key;
    return `Týden ${m[2]}/${m[1]}`;
  }
  function fmtDayCZ(d){
    return d.toLocaleDateString('cs-CZ', { weekday: 'short', day: '2-digit', month: '2-digit' }).replace(/^./, c=>c.toUpperCase());
  }
  function enhance(){
    const tbl = document.querySelector('table.table');
    if(!tbl || !tbl.tBodies || !tbl.tBodies[0]) return;
    const body = tbl.tBodies[0];
    const rows = Array.from(body.rows);
    if(rows.length===0) return;
    // detect date column
    let dateCol = 0;
    outer: for(let c=0;c<tbl.rows[0].cells.length;c++){
      for(let r=0;r<Math.min(6, rows.length);r++){
        const d = parseCZDate(rows[r].cells[c]?.innerText);
        if(d){ dateCol = c; break outer; }
      }
    }
    // sort
    rows.sort((ra,rb)=>{
      const da = parseCZDate(ra.cells[dateCol]?.innerText) || new Date(0);
      const db = parseCZDate(rb.cells[dateCol]?.innerText) || new Date(0);
      return +da - +db;
    });
    rows.forEach(r=>body.appendChild(r));
    // insert groups
    let lastWeek=null, lastDay=null;
    rows.forEach(row=>{
      const d = parseCZDate(row.cells[dateCol]?.innerText);
      if(!d) return;
      const wk = weekKey(d);
      if(wk!==lastWeek){
        const hr = body.insertRow(row.rowIndex);
        hr.className='ts-week-header'; const c=hr.insertCell(0); c.colSpan=tbl.rows[0].cells.length; c.innerHTML=`<div class="ts-week-row"><div class="ts-week-title">${fmtWeekLabel(wk)}</div><div class="ts-week-line"></div></div>`;
        lastWeek=wk; lastDay=null;
      }
      if(!lastDay || (+d!==+lastDay)){
        const dr = body.insertRow(row.rowIndex); dr.className='ts-day-sep'; const dc=dr.insertCell(0); dc.colSpan=tbl.rows[0].cells.length; dc.innerHTML=`<div class="ts-day-chip">${fmtDayCZ(d)}</div>`; lastDay=new Date(d);
      }
      row.classList.add('ts-data-row');
    });
  }
  if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', enhance); } else { enhance(); }
})();