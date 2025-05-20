// static/js/serviceworker.js
const CACHE_NAME = 'business-directory-v1';
const urlsToCache = [
  '/',
  '/offline.html',
  '/static/css/styles.css',
  '/static/js/main.js',
  '/static/images/logo.png',
  // Add other static files you want to cache
];

// Install the service worker and cache resources
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

// Serve cached resources when offline
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Return cached resource if found
        if (response) {
          return response;
        }
        // Otherwise, fetch from the network
        return fetch(event.request)
          .then((networkResponse) => {
            // Optionally cache the new resource for future use
            return caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, networkResponse.clone());
                return networkResponse;
              });
          })
          .catch(() => {
            // If both cache and network fail, serve a custom offline page
            return caches.match('/offline.html');
          });
      })
  );
});