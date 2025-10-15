
(function(){
  function moveLogin(){
    const all = Array.from(document.querySelectorAll('body *')).slice(0,600);
    let src = all.find(el => /Přihlášen/.test(el.textContent||''));
    if(!src) return;
    if(document.querySelector('.login-footer')) return;
    const badge = document.createElement('div');
    badge.className = 'login-footer';
    badge.textContent = src.textContent.trim();
    document.body.appendChild(badge);
    src.style.display = 'none';
  }
  if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', moveLogin); }
  else { moveLogin(); }
})();