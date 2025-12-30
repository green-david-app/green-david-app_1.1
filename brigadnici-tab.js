
// Hotfix: append "Brigádníci" tab into the top tabs on the main page.
// Safe: pure DOM manipulation, doesn't depend on React internals.
(function(){
  function addLink(){
    try{
      var tabs = document.querySelector('.tabs');
      if(!tabs) return;
      if(tabs.querySelector('a[href="/brigadnici.html"]')) return; // already there
      var a = document.createElement('a');
      a.href = '/brigadnici.html';
      a.textContent = 'Brigádníci';
      a.className = 'tab';
      tabs.appendChild(a);
    }catch(e){ console.warn('Hotfix brigadnici tab failed:', e); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', addLink);
  else addLink();

  // Re-apply after potential dynamic rerenders:
  setInterval(addLink, 1500);
})();
