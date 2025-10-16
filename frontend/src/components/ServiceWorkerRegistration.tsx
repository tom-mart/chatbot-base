'use client';

import { useEffect } from 'react';

export default function ServiceWorkerRegistration() {
  useEffect(() => {
    // Register service worker when component mounts
    if (typeof window !== 'undefined' && 'serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js', {
          scope: '/',
          updateViaCache: 'none',
        })
        .then((registration) => {
          console.log('Service Worker registered:', registration);
        })
        .catch((error: Error) => {
          console.error('Failed to register service worker:', error);
        });
    }
  }, []);

  return null; // This component doesn't render anything
}
