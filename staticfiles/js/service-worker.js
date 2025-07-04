const CACHE_NAME = 'swiftfind-v5';
const OFFLINE_URL = '/offline/';
const CACHEABLE_ASSETS = [
  OFFLINE_URL,
  '/static/css/styles.css',  // Ensure this exists
  '/static/js/main.js',     // Ensure this exists
  '/static/images/logo.png' // Ensure this exists
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        // Cache each file individually with error handling
        return Promise.all(
          CACHEABLE_ASSETS.map((url) => {
            return fetch(url, { credentials: 'same-origin' })
              .then((response) => {
                if (!response.ok) throw new Error(`Failed to fetch ${url}`);
                return cache.put(url, response);
              })
              .catch((err) => {
                console.warn(`Couldn't cache ${url}:`, err);
              });
          })
        );
      })
      .then(() => self.skipWaiting())
  );
});