
(function(){
  const STATE = { inserted:false };

  function el(tag, attrs, ...kids){
    const n = document.createElement(tag);
    if(attrs){ for(const [k,v] of Object.entries(attrs)){ if(k==='class'){ n.className=v; } else { n.setAttribute(k,v); } } }
    for(const k of kids){ if(k!=null) n.append(k); }
    return n;
  }

  function pickAnchor(){
    // Prefer card whose header contains Seznam / Přehled / List
    const cards = Array.from(document.querySelectorAll('.card'));
    for(const c of cards){
      const h = c.querySelector('.card-h');
      if(h && /(Seznam|Přehled|Zakázky|Zaměstnanci|Sklad|Úkoly|Uživatelé|Users|List)/i.test(h.textContent||"")){
        return c;
      }
    }
    return cards[1] || cards[0] || null;
  }

  function buildCard(){
    const card = el('div', {class:'card card-dark gd-search-card'});
    const cc = el('div', {class:'card-c'});
    const input = el('input', {id:'_gd_global_search', class:'inp', type:'search', placeholder:'Hledat…'});
    cc.append(input);
    card.append(cc);
    return {card, input};
  }

  function gatherTargets(){
    const sets = [];
    // Tables
    document.querySelectorAll('table').forEach(t=>{
      const b = t.tBodies && t.tBodies[0] || t.querySelector('tbody');
      if(b){
        const rows = Array.from(b.querySelectorAll('tr'));
        if(rows.length) sets.push(rows);
      }
    });
    // Lists of cards (fallback)
    const lists = document.querySelectorAll('.card-list, .jobs-list, .employees-list');
    lists.forEach(list=>sets.push(Array.from(list.children)));
    return sets;
  }

  function insertIfNeeded(){
    if(STATE.inserted) return;
    const anchor = pickAnchor() || document.querySelector('.card');
    const host = anchor && anchor.parentElement || document.body;
    const {card, input} = buildCard();
    host.insertBefore(card, anchor || host.firstChild);
    function apply(){
      const q = (input.value||'').toLowerCase().trim();
      const sets = gatherTargets();
      sets.forEach(rows => rows.forEach(row => {
        const text = (row.getAttribute('data-search') || row.innerText || '').toLowerCase();
        row.style.display = !q || text.includes(q) ? '' : 'none';
      }));
    }
    input.addEventListener('input', apply);
    // initial
    apply();
    STATE.inserted = true;
  }

  function init(){
    // Try now
    insertIfNeeded();
    // And watch for dynamic content
    const obs = new MutationObserver(()=>insertIfNeeded());
    obs.observe(document.documentElement, {childList:true, subtree:true});
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  }else{
    init();
  }
})();
