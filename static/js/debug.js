// Debug logger — loguje jen na localhost
window.DEBUG = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
window.debugLog = function() {
  if (window.DEBUG) {
    console.log.apply(console, arguments);
  }
};
