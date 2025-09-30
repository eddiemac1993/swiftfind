// static/js/sw.js
self.addEventListener('install', (event) => {
    event.waitUntil(self.skipWaiting());
});

self.addEventListener('push', (event) => {
    let title = 'SwiftFind';
    let body = 'You have a new notification';
    let url = '/';

    if (event.data) {
        try {
            const data = event.data.json(); // Try parsing JSON
            title = data.title || title;
            body = data.body || body;
            url = data.url || url;
        } catch (e) {
            // Fallback if payload is plain text
            body = event.data.text();
        }
    }

    const options = {
        body: body,
        icon: '/static/images/logo.png',
        data: { url: url }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});
