// === Mobile-first FullCalendar config (green-david app) ===
document.addEventListener('DOMContentLoaded', function() {
  var el = document.getElementById('calendar');
  if (!el) return;

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