
(function(){
  try {
    var show = false;
    var qs = new URLSearchParams(location.search);
    if (qs.get('tab') === 'jobs') show = true;
    if (!show && document.body && document.body.innerText && document.body.innerText.indexOf('Nová zakázka') !== -1) {
      show = true;
    }
    var cta = document.getElementById('archive-cta');
    if (cta && show) cta.style.display = '';
  } catch(e){}
})();
