// Service Worker simplificado para Escentopia (v2)
const CACHE_NAME = "escentopia-cache-v2"

// Instalación del Service Worker
self.addEventListener("install", (event) => {
  console.log("Service Worker v2 instalado")
  self.skipWaiting() // Forzar activación inmediata
})

// Activación del Service Worker
self.addEventListener("activate", (event) => {
  console.log("Service Worker v2 activado")

  // Limpiar cachés antiguas
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log("Eliminando caché antigua:", cacheName)
            return caches.delete(cacheName)
          }
        }),
      )
    }),
  )

  // Tomar control inmediatamente
  event.waitUntil(clients.claim())
})

// Estrategia de caché: Network First, sin cachear nada por ahora
self.addEventListener("fetch", (event) => {
  // No interceptar peticiones a la API
  if (event.request.url.includes("/productos")) {
    return
  }

  // Simplemente pasar la solicitud a la red
  event.respondWith(
    fetch(event.request).catch(() => {
      // Si falla la red, intentar desde caché
      return caches.match(event.request)
    }),
  )
})
