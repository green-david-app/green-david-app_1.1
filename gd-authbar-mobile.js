
(function(){
  function mm(q){ try { return window.matchMedia(q).matches; } catch(e){ return false; } }
  if (!mm('(max-width: 768px)')) return;

  // Find "Odhlásit" button/link anywhere in the header
  var logout = Array.from(document.querySelectorAll('button, a, input[type="button"], input[type="submit"]'))
    .find(function(el){
      var t = (el.value || el.textContent || '').trim().toLowerCase();
      return /odhlásit|odhlasit/.test(t);
    });
  if (!logout) return;

  // Create or reuse #authBar container
  var pill = document.getElementById('authBar');
  if (!pill){
    pill = document.createElement('div');
    pill.id = 'authBar';
    // minimal inline style in case CSS doesn't load (we also add CSS file)
    pill.style.position = 'fixed';
    pill.style.right = '12px';
    pill.style.bottom = '12px';
    pill.style.zIndex = '1000';
    pill.style.padding = '8px 12px';
    pill.style.borderRadius = '12px';
    pill.style.background = 'rgba(20,28,23,.86)';
    pill.style.color = '#fff';
    pill.style.display = 'flex';
    pill.style.gap = '8px';
    pill.style.alignItems = 'center';
    document.body.appendChild(pill);
  }

  // Try to grab a "Přihlášen: ..." text and move/hide it
  var authTextNode = Array.from(document.querySelectorAll('header * , .header * , nav * , body *'))
    .find(function(el){
      if (!el || el === logout) return false;
      var t = (el.textContent || '').trim().toLowerCase();
      return /přihlášen|prihlasen|úkoly|ukoly/.test(t);
    });

  if (authTextNode){
    // clone a short label, then hide the original
    var shortSpan = document.createElement('span');
    shortSpan.className = 'auth-text';
    shortSpan.textContent = '';
    try { authTextNode.style.display = 'none'; } catch(e){}
    pill.appendChild(shortSpan);
  }

  // Move the logout button inside the pill
  pill.appendChild(logout);
})();
