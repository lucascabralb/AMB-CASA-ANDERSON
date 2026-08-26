// Service worker do Casa Anderson — cache básico para o app abrir
// mesmo com internet instável (os dados dos dispositivos continuam
// exigindo conexão real com o backend, isso aqui só cacheia a
// interface: HTML, ícones, manifest).

const CACHE_NAME = 'casa-anderson-v1';
const ASSETS_TO_CACHE = [
  './casa-anderson-app.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Nunca cachear chamadas de API para o backend (dados sempre precisam
  // ser em tempo real) — só cacheia os arquivos estáticos do app.
  if (req.method !== 'GET' || req.url.includes('railway.app')) {
    return;
  }

  event.respondWith(
    caches.match(req).then((cached) => {
      const networkFetch = fetch(req)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(req, clone));
          }
          return response;
        })
        .catch(() => cached);
      return cached || networkFetch;
    })
  );
});
