const CACHE_NAME = 'swiftfind-v7';
const ESSENTIAL_URLS = [
  '/',
  '/static/css/styles.css',
  '/static/js/main.js'
  // Removed problematic files from initial cache list
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        // Only cache files we know exist
        return cache.addAll(ESSENTIAL_URLS)
          .then(() => {
            // Attempt to cache optional files separately
            return Promise.all([
              cacheOptionalFile(cache, '/static/images/logo.png'),
              cacheOptionalFile(cache, '/offline/')
            ]);
          });
      })
      .then(() => self.skipWaiting())
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