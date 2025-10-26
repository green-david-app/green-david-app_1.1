// Calendar Events Patch v3 — long titles visibility + modal
(function(){
  function enhance(){
    const sel = '.event, .event-item, .calendar-event, .badge, .chip';
    document.querySelectorAll(sel).forEach(el => {
      if (el.dataset.gdEnhanced) return;
      el.dataset.gdEnhanced = '1';
      const full = el.getAttribute('data-title') || el.getAttribute('title') || el.textContent.trim();
      if (full) el.setAttribute('title', full);
      el.addEventListener('click', () => openModal(full));
    });
  }
  let dlg;
  function ensureDialog(){
    if (dlg) return dlg;
    dlg = document.createElement('dialog');
    dlg.className = 'gd-dialog';
    dlg.innerHTML = '<h3>Detail</h3><div class=\"gd-body\"></div><button class=\"gd-close\">Zavřít</button>';
    document.body.appendChild(dlg);
    dlg.querySelector('.gd-close').addEventListener('click', ()=> dlg.close());
    return dlg;
  }
  function openModal(text){
    const d = ensureDialog();
    d.querySelector('.gd-body').textContent = text || '';
    if (typeof d.showModal === 'function') d.showModal(); else d.style.display='block';
  }
  const ro = new MutationObserver(enhance);
  ro.observe(document.documentElement, {subtree:true, childList:true});
  enhance();
})();