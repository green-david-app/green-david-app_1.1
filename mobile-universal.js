// universal mobile helper (green david app)
(function () {
  // 1) Real 100vh on mobile (uses CSS variable --vh)
  function setVh() {
    const vh = window.innerHeight * 0.01;
    document.documentElement.style.setProperty('--vh', `${vh}px`);
  }
  setVh();
  window.addEventListener('resize', setVh);
  window.addEventListener('orientationchange', setVh);

  // 2) Add meta viewport if missing (sensible defaults)
  (function ensureViewport() {
    let meta = document.querySelector('meta[name="viewport"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'viewport';
      meta.content = 'width=device-width, initial-scale=1, viewport-fit=cover';
      document.head.appendChild(meta);
    } else if (!/viewport-fit=cover/.test(meta.content)) {
      meta.content = meta.content + ', viewport-fit=cover';
    }
  })();

  // 3) iOS: prevent keyboard from pushing inputs under fixed bars
  function scrollIntoViewIfNeeded(el) {
    if (!el) return;
    const r = el.getBoundingClientRect();
    const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
    if (r.bottom > vh - 10) el.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }
  document.addEventListener('focusin', (e) => {
    const t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) {
      setTimeout(() => scrollIntoViewIfNeeded(t), 50);
    }
  });

  // 4) CSS class to use full height: height: calc(var(--vh) * 100);
  document.documentElement.classList.add('vh-ready');
})();
