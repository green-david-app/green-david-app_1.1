
(function(){
  function el(t,a,...k){const n=document.createElement(t);if(a){for(const[i,v]of Object.entries(a)){i==='class'?n.className=v:n.setAttribute(i,v)}}k.forEach(x=>x!=null&&n.append(x));return n}
  function findCard(){const cs=[...document.querySelectorAll('.card')];for(const c of cs){const h=c.querySelector('.card-h');if(h&&/Seznam/i.test(h.textContent))return c}return cs[1]||cs[0]||null}
  function createCard(){const h=el('div',{class:'card card-dark gd-search-card'});const c=el('div',{class:'card-c'});const i=el('input',{type:'search',placeholder:'Hledat…',class:'inp',id:'_gd_search'});c.append(i);h.append(c);return{h,i}}
  function sets(){const s=[];document.querySelectorAll('table').forEach(t=>{const b=t.tBodies&&t.tBodies[0]||t.querySelector('tbody');if(b){const r=[...b.querySelectorAll('tr')];if(r.length)s.push(r)}});const list=document.querySelector('.card-list,.jobs-list,.employees-list');if(list)s.push([...list.children]);return s}
  function attach(){const where=findCard()||document.querySelector('.card');const {h,i}=createCard();if(where&&where.parentElement){where.parentElement.insertBefore(h,where)}else{document.body.insertBefore(h,document.body.firstChild)}const S=sets();function apply(){const q=(i.value||'').toLowerCase().trim();S.forEach(rs=>rs.forEach(tr=>{const t=(tr.getAttribute('data-search')||tr.innerText||'').toLowerCase();tr.style.display=!q||t.includes(q)?'':''}))}i.addEventListener('input',apply);apply()}
  function ok(){const txt=(location.pathname+' '+document.body.innerText).toLowerCase();return /zam[eě]stnanci|zak[aá]zky|úkoly|ukoly|sklad|uživatel[eů]|uzivatele/.test(txt)}
  function init(){if(!ok())return;attach()}if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init)}else{init()}
})();
