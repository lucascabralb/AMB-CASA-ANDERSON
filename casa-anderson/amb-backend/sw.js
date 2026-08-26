// Service worker mínimo — necessário para o navegador considerar
// o app um PWA instalável (exigência técnica, não faz cache agressivo).
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
self.addEventListener('fetch', () => {}); // deixa tudo passar direto para a rede
