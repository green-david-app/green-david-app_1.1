// === Mobile-first FullCalendar config (green-david app) ===
document.addEventListener('DOMContentLoaded', function() {
  // 1) Ensure viewport meta exists early
  (function ensureViewport(){
    var head = document.head || document.getElementsByTagName('head')[0];
    if (!head) return;
    var hasViewport = !!document.querySelector('meta[name="viewport"]');
    if (!hasViewport) {
      var m = document.createElement('meta');
      m.setAttribute('name', 'viewport');
      m.setAttribute('content', 'width=device-width, initial-scale=1');
      head.appendChild(m);
    }
  })();

  // 2) Ensure responsive.css is linked
  (function ensureResponsiveCss(){
    var head = document.head || document.getElementsByTagName('head')[0];
    if (!head) return;
    var hasCss = [].slice.call(document.querySelectorAll('link[rel="stylesheet"]'))
      .some(function(l){ return (l.getAttribute('href')||'').indexOf('/static/css/responsive.css') !== -1; });
    if (!hasCss) {
      var link = document.createElement('link');
      link.setAttribute('rel', 'stylesheet');
      link.setAttribute('href', '/static/css/responsive.css');
      head.appendChild(link);
    }
  })();

  var el = document.getElementById('calendar');
  if (!el) return;

  // 3) Wrap calendar in .calendar-wrapper if not wrapped
  (function ensureWrapper(){
    if (!el.parentElement || !el.parentElement.classList.contains('calendar-wrapper')) {
      var wrap = document.createElement('div');
      wrap.className = 'calendar-wrapper';
      el.parentNode.insertBefore(wrap, el);
      wrap.appendChild(el);
    }
  })();

  var isMobile = window.matchMedia('(max-width: 768px)').matches;

  var calendar = new FullCalendar.Calendar(el, {
    initialView: isMobile ? 'listWeek' : 'dayGridMonth',
    height: 'auto',
    contentHeight: 'auto',
    expandRows: true,
    handleWindowResize: true,
    stickyHeaderDates: true,
    dayMaxEvents: true,
    navLinks: true,

    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: isMobile ? 'listWeek,dayGridMonth' : 'dayGridMonth,timeGridWeek,timeGridDay'
    },

    windowResize: function() {
      var nowMobile = window.matchMedia('(max-width: 768px)').matches;
      if (nowMobile && calendar.view.type !== 'listWeek') {
        calendar.changeView('listWeek');
      } else if (!nowMobile && calendar.view.type === 'listWeek') {
        calendar.changeView('dayGridMonth');
      }
    },

    // preserve existing events source if the app uses it; this is a stub to avoid breaking code
    events: window.CALENDAR_EVENTS_URL || [],
  });

  calendar.render();

  // Ensure no horizontal scroll on parent containers
  var parents = [];
  var node = el;
  while (node && node !== document.body) {
    parents.push(node);
    node = node.parentElement;
  }
  parents.forEach(function(p) {
    p.style.overflowX = 'hidden';
  });
});