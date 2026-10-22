// Cortex JOSY EI — service worker (PWA).
// Cache de base : icônes et pages déjà vues, pour que l'application s'ouvre vite.
// Les pages passent toujours par le réseau d'abord (données à jour) ; le cache ne sert que
// si l'interface locale est arrêtée. Les notifications sont affichées par la page
// (onglet ouvert ou application installée ouverte) via showNotification.
const CACHE = "cortex-v3";  // v3 : icône ronde recadrée + version maskable
const STATIQUES = ["/icon-192.png", "/icon-512.png", "/icon-maskable-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(STATIQUES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys()
    .then((cles) => Promise.all(cles.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;  // actions (Valider, Discuter…) : jamais de cache
  const url = new URL(req.url);
  if (STATIQUES.includes(url.pathname)) {
    e.respondWith(caches.match(req).then((r) => r || fetch(req)));
    return;
  }
  if (req.mode === "navigate") {
    e.respondWith(fetch(req).then((r) => {
      const copie = r.clone();
      caches.open(CACHE).then((c) => c.put(req, copie));
      return r;
    }).catch(() => caches.match(req).then((r) => r || new Response(
      "<meta charset=utf-8><body style='background:#12141a;color:#e8eaf0;font:16px system-ui;padding:24px'>" +
      "<h1>Cortex hors ligne</h1><p>L'interface locale ne répond pas. Lance « Cortex » sur ton PC puis réessaie.</p>",
      { headers: { "Content-Type": "text/html; charset=utf-8" } }))));
  }
});

self.addEventListener("notificationclick", (e) => {
  e.notification.close();
  const cible = (e.notification.data && e.notification.data.url) || "/";
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((fen) => {
    for (const f of fen) { if ("focus" in f) { f.navigate(cible); return f.focus(); } }
    return self.clients.openWindow(cible);
  }));
});
