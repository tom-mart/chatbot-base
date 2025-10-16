// Keep service worker alive
self.addEventListener('install', function(event) {
  console.log('[SW] Service worker installed');
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  console.log('[SW] Service worker activated');
  event.waitUntil(self.clients.claim());
});

// Handle push events with better error handling and logging
self.addEventListener('push', function (event) {
  console.log('[SW] Push event received', event);
  
  if (!event.data) {
    console.log('[SW] Push event has no data');
    return;
  }
  
  try {
    const data = event.data.json();
    console.log('[SW] Push notification data:', data);
    
    const options = {
      body: data.body,
      icon: data.icon || '/web-app-manifest-192x192.png',
      badge: data.badge || '/favicon-96x96.png',
      vibrate: [100, 50, 100],
      tag: data.tag || 'notification',
      requireInteraction: data.requireInteraction || false,
      // Add timestamp to track when notification was received
      timestamp: Date.now(),
      data: {
        url: data.url || '/',
        notificationId: data.data?.notificationId,
        notificationType: data.data?.notificationType,
        receivedAt: new Date().toISOString(),
        ...data.data,
      },
    };
    
    // Add action buttons if provided
    if (data.actions && data.actions.length > 0) {
      options.actions = data.actions;
    }
    
    // Show notification and keep service worker alive
    event.waitUntil(
      self.registration.showNotification(data.title, options)
        .then(() => {
          console.log('[SW] Notification shown successfully');
          // Try to wake up the app if it's in the background
          return self.clients.matchAll({ type: 'window', includeUncontrolled: true });
        })
        .then((clients) => {
          console.log('[SW] Found', clients.length, 'client windows');
          // Notify any open clients about the new notification
          clients.forEach(client => {
            client.postMessage({
              type: 'PUSH_RECEIVED',
              notification: data
            });
          });
        })
        .catch((error) => {
          console.error('[SW] Error showing notification:', error);
        })
    );
  } catch (error) {
    console.error('[SW] Error parsing push data:', error);
  }
});

self.addEventListener('notificationclick', function (event) {
  console.log('Notification click received:', event.action)
  event.notification.close()
  
  const notificationData = event.notification.data || {}
  const notificationId = notificationData.notificationId
  
  // Handle snooze action
  if (event.action === 'snooze' && notificationId) {
    event.waitUntil(
      fetch('/api/notifications/scheduled/' + notificationId + '/snooze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({})
      })
      .then(response => {
        if (response.ok) {
          console.log('Notification snoozed successfully')
          // Show a confirmation notification
          return self.registration.showNotification('Snoozed', {
            body: 'You\'ll be reminded again in 30 minutes',
            icon: '/web-app-manifest-192x192.png',
            tag: 'snooze-confirmation',
            requireInteraction: false,
          })
        } else {
          console.error('Failed to snooze notification')
        }
      })
      .catch(error => {
        console.error('Error snoozing notification:', error)
      })
    )
    return
  }
  
  // Default action: open the URL
  const urlToOpen = notificationData.url || '/'
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then(function (clientList) {
        // Check if there's already a window open
        for (let i = 0; i < clientList.length; i++) {
          const client = clientList[i]
          if (client.url === new URL(urlToOpen, self.location.origin).href && 'focus' in client) {
            return client.focus()
          }
        }
        // If no window is open, open a new one
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen)
        }
      })
  )
})
