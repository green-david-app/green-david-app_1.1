// Green David App - PWA Initialization
// Injected by every page via <script src="/static/pwa-init.js">
// =============================================

(function() {
  'use strict';

  // ── 1. Inject <head> meta tags for PWA ──
  const head = document.head;

  function addMeta(name, content) {
    if (!document.querySelector(`meta[name="${name}"]`)) {
      const meta = document.createElement('meta');
      meta.name = name;
      meta.content = content;
      head.appendChild(meta);
    }
  }

  function addLink(rel, href, extra) {
    if (!document.querySelector(`link[rel="${rel}"][href="${href}"]`)) {
      const link = document.createElement('link');
      link.rel = rel;
      link.href = href;
      if (extra) Object.assign(link, extra);
      head.appendChild(link);
    }
  }

  // Manifest
  addLink('manifest', '/manifest.json');

  // Theme color
  addMeta('theme-color', '#1a7f37');
  addMeta('background-color', '#0d1117');

  // Apple PWA meta tags
  addMeta('apple-mobile-web-app-capable', 'yes');
  addMeta('apple-mobile-web-app-status-bar-style', 'black-translucent');
  addMeta('apple-mobile-web-app-title', 'Green David');
  addMeta('mobile-web-app-capable', 'yes');

  // Apple touch icons
  addLink('apple-touch-icon', '/static/icons/icon-152x152.png');
  addLink('apple-touch-icon', '/static/icons/icon-192x192.png', { sizes: '192x192' });

  // ── 2. Register Service Worker ──
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', async () => {
      try {
        const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
        console.log('[PWA] Service Worker registered, scope:', reg.scope);

        // Check for updates periodically (every 60 minutes)
        setInterval(() => reg.update(), 60 * 60 * 1000);

        // Handle SW update
        reg.addEventListener('updatefound', () => {
          const newSW = reg.installing;
          newSW.addEventListener('statechange', () => {
            if (newSW.state === 'activated') {
              // Show subtle update notification
              if (window.showToast) {
                window.showToast('Aplikace aktualizována', 'info');
              }
            }
          });
        });
      } catch (err) {
        console.warn('[PWA] SW registration failed:', err);
      }
    });
  }

  // ── 3. Install prompt (Add to Home Screen) ──
  let deferredPrompt = null;

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    console.log('[PWA] Install prompt available');
    
    // Show install button if exists
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.style.display = 'inline-flex';
      installBtn.addEventListener('click', promptInstall);
    }

    // Dispatch custom event for any UI component to catch
    window.dispatchEvent(new CustomEvent('pwa-install-available'));
  });

  window.addEventListener('appinstalled', () => {
    deferredPrompt = null;
    console.log('[PWA] App installed');
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) installBtn.style.display = 'none';
  });

  // Public: trigger install prompt
  window.promptPWAInstall = promptInstall;
  async function promptInstall() {
    if (!deferredPrompt) return false;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    deferredPrompt = null;
    return result.outcome === 'accepted';
  }

  // Public: check if running as installed PWA
  window.isPWA = function() {
    return window.matchMedia('(display-mode: standalone)').matches
      || window.navigator.standalone === true;
  };

  // ── 4. Online/offline indicator ──
  function updateOnlineStatus() {
    document.documentElement.classList.toggle('is-offline', !navigator.onLine);
    if (!navigator.onLine && window.showToast) {
      window.showToast('Jste offline', 'warning');
    }
  }
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);

})();
