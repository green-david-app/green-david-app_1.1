// common-footer.js — sticky footer + auto-load CSS
(function(){
  try{
    // load CSS if missing
    const present = Array.from(document.styleSheets||[]).some(s => (s.href||'').includes('mobile-override.css'));
    if(!present){ const l=document.createElement('link'); l.rel='stylesheet'; l.href='/mobile-override.css'; document.head.appendChild(l); }

    function ensureFooter(){
      let el = document.getElementById('meFooter');
      if(!el){
        el = document.createElement('div');
        el.id='meFooter'; el.className='me-footer'; el.style.display='none';
        el.innerHTML='<div class="left" id="meText"></div><div class="right"><a href=\"/\">Domů</a></div>';
        (document.querySelector('.container')||document.body).appendChild(el);
      }
    }
    function fill(){
      fetch('/api/me').then(r=>r.json()).then(me=>{
        const email = me && me.email ? String(me.email) : '';
        const name  = (me && (me.name || me.fullname || me.title)) || '';
        const who = (name ? name+' ' : '') + (email? '('+email+')':'');
        const txt = document.getElementById('meText'); const box = document.getElementById('meFooter');
        if(txt && box){ txt.textContent = who ? 'Přihlášen: '+who : 'Přihlášený uživatel neznámý'; box.style.display='flex'; }
      }).catch(()=>{});
    }
    document.addEventListener('DOMContentLoaded', ()=>{ ensureFooter(); fill(); });
  }catch(e){ /* ignore */ }
})();