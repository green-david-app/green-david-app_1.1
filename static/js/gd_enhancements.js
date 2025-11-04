
(function(){
  function h(tag, attrs, ...kids){
    const el = document.createElement(tag);
    if(attrs) for(const [k,v] of Object.entries(attrs)) (k==='class'? el.className=v : el.setAttribute(k,v));
    for(const k of kids) el.append(k);
    return el;
  }

  function addSearch(container, getItems, renderFilter){
    if(!container || container.querySelector('.gd-search')) return;
    const holder = h('div', {class: 'gd-search'});
    const input  = h('input', {type:'search', placeholder: 'Hledat…'});
    holder.append(input);
    (renderFilter||((c)=>c.prepend(holder)))(container);

    function apply(){
      const q = (input.value||'').toLowerCase().trim();
      const items = getItems();
      items.forEach(el=>{
        const text = el.getAttribute('data-search') || el.textContent;
        el.style.display = !q || (text||'').toLowerCase().includes(q) ? '' : 'none';
      });
    }
    input.addEventListener('input', apply);
    apply();
  }

  function tryEmployees(){
    if(!/employees|zam[eě]stnanci/i.test(location.pathname+document.body.innerText)) return;
    // Variant A: table
    const table = document.querySelector('table') || document.querySelector('.tbl,.table');
    const tbody = table && (table.tBodies[0] || table.querySelector('tbody'));
    if(tbody){
      addSearch(table.parentElement||table, ()=>Array.from(tbody.querySelectorAll('tr')), (c)=>c.insertBefore(c.querySelector('.gd-search')||h('div'), c.firstChild).replaceWith(h('div')));
      return true;
    }
    // Variant B: cards list
    const list = document.querySelector('.card-list, .cards, .jobs-list, .employees-list');
    if(list){
      addSearch(list.parentElement||list, ()=>Array.from(list.children));
      return true;
    }
  }

  function tryJobs(){
    if(!/jobs|zak[aá]zky/i.test(location.pathname+document.body.innerText)) return;
    const list = document.querySelector('.card-list, .cards');
    if(list){
      addSearch(list.parentElement||list, ()=>Array.from(list.children));
      return true;
    }
    // fallback: table
    const table = document.querySelector('table') || document.querySelector('.tbl,.table');
    const tbody = table && (table.tBodies[0] || table.querySelector('tbody'));
    if(tbody){
      addSearch(table.parentElement||table, ()=>Array.from(tbody.querySelectorAll('tr')), (c)=>c.insertBefore(c.querySelector('.gd-search')||h('div'), c.firstChild).replaceWith(h('div')));
      return true;
    }
  }

  function init(){
    tryEmployees();
    tryJobs();
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
