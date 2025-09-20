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
// In your main JS file
if ('serviceWorker' in navigator && 'PushManager' in window) {
    navigator.serviceWorker.register('/sw.js')
        .then(function(registration) {
            console.log('ServiceWorker registration successful');
            return registration.pushManager.getSubscription()
                .then(function(subscription) {
                    if (subscription) return subscription;
                    return registration.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
                    });
                });
        })
        .catch(function(err) {
            console.log('ServiceWorker registration failed: ', err);
        });
}