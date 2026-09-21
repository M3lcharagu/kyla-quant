const CACHE_NAME = 'kyla-web-v1';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './service-worker.js',
  './data/dashboard.json',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) =>
      Promise.all(APP_SHELL.map((asset) => cache.add(asset).catch(() => undefined)))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  const isDataEndpoint = url.pathname.includes('/data/') || url.pathname.endsWith('/paper_trades.json');

  if (isDataEndpoint) {
    // Data is allowed to go stale only when the network is unavailable.
    event.respondWith(
      fetch(event.request).then((response) => {
        if (response.ok) {
          const copy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
        }
        return response;
      }).catch(() => caches.match(event.request).then((cached) =>
        cached || new Response('{"error":"offline","message":"No cached data available."}', {
          headers: { 'Content-Type': 'application/json' },
          status: 503
        })
      ))
    );
    return;
  }

  // App shell assets use cache-first for fast phone launches.
  event.respondWith(
    caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
      if (response.ok && url.origin === self.location.origin) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
      }
      return response;
    }))
  );
});
