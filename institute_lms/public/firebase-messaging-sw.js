/* Public browser configuration only. Never put Admin credentials here. */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.stopImmediatePropagation();
  event.waitUntil(clients.openWindow(new URL('/campus', self.location.origin).href));
});
importScripts('https://www.gstatic.com/firebasejs/13.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/13.0.0/firebase-messaging-compat.js');
const config = JSON.parse(new URL(self.location.href).searchParams.get('config'));
if (config?.projectId !== 'sisu-lms') throw new Error('Unexpected Firebase project');
firebase.initializeApp(config);
firebase.messaging();
// Notification payloads are displayed by Firebase in the background. Do not display twice.
