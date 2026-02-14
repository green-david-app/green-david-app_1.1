// Green David App - PWA Service Worker
// =====================================
const CACHE_VERSION = 'gd-v1';
const STATIC_CACHE = `static-${CACHE_VERSION}`;
const API_CACHE = `api-${CACHE_VERSION}`;

// Static assets to pre-cache on install
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/jobs.html',
  '/job-detail.html',
  '/tasks.html',
  '/team.html',
  '/static/style.css',
  '/static/css/app.css',
  '/static/css/glass-design.css',
  '/static/css/sidebar.css',
  '/static/css/responsive.css',
  '/static/css/tasks-design-system.css',
  '/static/css/global-search.css',
  '/static/css/layout.css',
  '/static/icons.css',
  '/static/app-header.js',
  '/static/app-sidebar.js',
  '/static/global-search.js',
  '/static/loading.js',
  '/static/toast.js',
  '/app-settings.js',
  '/static/img/logo.jpg',
  '/static/icons/icon-192x192.png',
  '/logo.svg',
  '/offline.html'
];

// ── Install: pre-cache static shell ──
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        // Don't fail install if some assets are missing
        return Promise.allSettled(
          PRECACHE_URLS.map(url => 
            cache.add(url).catch(err => console.warn(`[SW] Skip precache: ${url}`))
          )
        );
      })
      .then(() => self.skipWaiting())
  );
});

// ── Activate: clean old caches ──
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then(keys => 
      Promise.all(
        keys.filter(key => key !== STATIC_CACHE && key !== API_CACHE)
            .map(key => {
              console.log(`[SW] Removing old cache: ${key}`);
              return caches.delete(key);
            })
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: smart caching strategy ──
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Skip chrome-extension and other non-http
  if (!url.protocol.startsWith('http')) return;

  // Strategy 1: API calls → Network-first, cache fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstWithCache(event.request, API_CACHE));
    return;
  }
  
  // Strategy 2: Static assets → Cache-first, network fallback
  if (isStaticAsset(url.pathname)) {
    event.respondWith(cacheFirstWithNetwork(event.request, STATIC_CACHE));
    return;
  }
  
  // Strategy 3: HTML pages → Network-first with offline fallback
  if (event.request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(networkFirstWithOffline(event.request));
    return;
  }
  
  // Default: network with cache fallback
  event.respondWith(networkFirstWithCache(event.request, STATIC_CACHE));
});

// ── Caching Strategies ──

// Cache-first: fast for static assets
async function cacheFirstWithNetwork(request, cacheName) {
  const cached = await caches.match(request);
  if (cached) return cached;
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    return new Response('Offline', { status: 503 });
  }
}

// Network-first: fresh data for API
async function networkFirstWithCache(request, cacheName) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    return new Response(JSON.stringify({ ok: false, error: 'offline' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Network-first with offline page fallback for HTML
async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (err) {
    const cached = await caches.match(request);
    if (cached) return cached;
    // Show offline page
    const offline = await caches.match('/offline.html');
    if (offline) return offline;
    return new Response('<h1>Offline</h1><p>Green David App je momentálně offline.</p>', {
      status: 503,
      headers: { 'Content-Type': 'text/html; charset=utf-8' }
    });
  }
}

// Helper: detect static assets
function isStaticAsset(pathname) {
  return /\.(css|js|png|jpg|jpeg|gif|svg|woff2?|ttf|ico)(\?.*)?$/.test(pathname) 
    || pathname.startsWith('/static/');
}

// ── Push Notifications ──
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'Green David';
  const options = {
    body: data.body || '',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/icon-96x96.png',
    tag: data.tag || 'notification',
    vibrate: [200, 100, 200],
    data: data,
    actions: data.actions || []
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const data = event.notification.data || {};
  const targetUrl = data.url || '/';
  
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(clients => {
        // Focus existing window if possible
        for (const client of clients) {
          if (client.url.includes(targetUrl) && 'focus' in client) {
            return client.focus();
          }
        }
        // Otherwise open new window
        if (self.clients.openWindow) {
          return self.clients.openWindow(targetUrl);
        }
      })
  );
});

// ── Background Sync (for offline form submissions) ──
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-timesheets') {
    event.waitUntil(syncTimesheets());
  }
});

async function syncTimesheets() {
  // Future: replay queued timesheet submissions
  console.log('[SW] Background sync: timesheets');
}

// ── Periodic cache cleanup ──
self.addEventListener('message', (event) => {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
  }
  if (event.data === 'clearCache') {
    caches.keys().then(keys => keys.forEach(key => caches.delete(key)));
  }
});

console.log('[SW] Service Worker loaded');
