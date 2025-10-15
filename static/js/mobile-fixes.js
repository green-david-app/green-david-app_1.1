
(function(){
  const isMobile = window.matchMedia("(max-width: 767.98px)").matches;
  if(isMobile){
    // Hide auth/status banners by content (failsafe)
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
    const toHide = [];
    while(walker.nextNode()){
      const el = walker.currentNode;
      try{
        const txt = (el.innerText || "").trim();
        if(txt.startsWith("Přihlášený uživatel")){
          toHide.push(el);
        }
      }catch(e){}
    }
    toHide.forEach(el => { el.style.display = "none"; el.ariaHidden = "true"; });
    // If a stray 'Admin' text node sits near the brand, hide its container on mobile
    document.querySelectorAll('a,button,span,b,div').forEach(el => {
      if(/^\s*Admin\s*$/i.test((el.textContent||"").trim())){
        el.style.display = "none";
      }
    });
  }
})();
