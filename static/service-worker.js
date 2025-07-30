const CACHE_NAME = 'swiftfind-cache-v1';
const OFFLINE_URL = '/offline.html'; // Create this file if needed

const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  // Add other essential files
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache)
          .then(() => {
            // Only cache offline page if it exists
            return fetch(OFFLINE_URL)
              .then(response => {
                if (response.ok) return cache.add(OFFLINE_URL);
                return Promise.resolve();
              })
              .catch(() => Promise.resolve());
          });
      })
  );
});

// Helper function to cache files that might not exist
function cacheOptionalFile(cache, url) {
  return fetch(url, { credentials: 'include' })
    .then(response => {
      if (!response.ok) throw new Error('File not found');
      return cache.put(url, response);
    })
    .catch(err => {
      console.warn(`Optional file not cached: ${url}`, err);
      return Promise.resolve(); // Continue despite failure
    });
}