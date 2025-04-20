// Service Worker para Escentopia
const CACHE_NAME = "escentopia-cache-v1"

// Archivos a cachear inicialmente
const urlsToCache = [
  "/",
  "/index.html",
  "/static/css/styles.css",
  "/static/js/nav.js",
  "/static/js/funciones-globales.js",
  "/static/images/producto1.jpg",
  "/static/images/producto2.jpg",
]

// Instalación del Service Worker
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("Cache abierto")
      return cache.addAll(urlsToCache)
    }),
  )
})

// Activación del Service Worker
self.addEventListener("activate", (event) => {
  const cacheWhitelist = [CACHE_NAME]
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName)
          }
        }),
      )
    }),
  )
})

// Estrategia de caché: Network First, fallback to cache
self.addEventListener("fetch", (event) => {
  // No interceptar peticiones a la API
  if (event.request.url.includes("/productos")) {
    return
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        // Clonar la respuesta para poder usarla y guardarla
        const responseToCache = response.clone()

        caches.open(CACHE_NAME).then((cache) => {
          // Solo cachear respuestas exitosas
          if (event.request.method === "GET" && response.status === 200) {
            cache.put(event.request, responseToCache)
          }
        })

        return response
      })
      .catch(() => {
        // Si falla la red, intentar desde caché
        return caches.match(event.request)
      }),
  )
})
