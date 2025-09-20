const CACHE_NAME = 'swiftfind-pwa-v1';
const OFFLINE_URL = '/offline/';
const CACHEABLE_URLS = [
    OFFLINE_URL,
    '/static/css/styles.css',
    '/static/js/main.js',
    '/static/images/logo.png',
    // Add other essential URLs
];

// Install - Cache critical resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(CACHEABLE_URLS))
            .then(() => self.skipWaiting())
    );
});

// Activate - Clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => 
            Promise.all(
                cacheNames.map((cache) => 
                    cache !== CACHE_NAME ? caches.delete(cache) : null
                )
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch - Smart caching strategy
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;
    
    // Handle HTML requests with network-first strategy
    if (event.request.headers.get('accept').includes('text/html')) {
        event.respondWith(
            fetch(event.request)
                .catch(() => caches.match(OFFLINE_URL))
        );
        return;
    }
    
    // Handle static assets with cache-first strategy
    event.respondWith(
        caches.match(event.request)
            .then((cached) => cached || fetch(event.request))
    );
});