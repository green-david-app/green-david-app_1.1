// Načte jobs-patch.js automaticky, pokud stránka obsahuje prvky z listu zakázek
(function(){
  function needsJobsPatch(){
    return !!document.querySelector('[data-action="delete-job"], .job-row, #jobs-table, [data-jobs-list]');
  }
  function inject(src){
    var s=document.createElement('script'); s.src=src; s.defer=true; document.head.appendChild(s);
  }
  if(document.readyState==='loading'){
    document.addEventListener('DOMContentLoaded', function(){
      if(needsJobsPatch()) inject('/static/patch/jobs-patch.js?v=20251017');
    });
  } else {
    if(needsJobsPatch()) inject('/static/patch/jobs-patch.js?v=20251017');
  }
})();