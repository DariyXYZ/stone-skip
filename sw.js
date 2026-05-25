const CACHE = 'stone-skipping-game-v101';
const FILES = [
  './',
  './index.html',
  './stone-skipping-game.html',
  './stone-skipping-shop-assets-editor.html',
  './assets/stone-skipping-splash-cover.txt',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const request = e.request;
  const accept = request.headers.get('accept') || '';
  const isPageRequest = request.mode === 'navigate' || accept.includes('text/html');

  if (isPageRequest) {
    e.respondWith(
      fetch(request).catch(() => caches.match(request))
    );
    return;
  }

  e.respondWith(
    caches.match(request).then(r => r || fetch(request))
  );
});
