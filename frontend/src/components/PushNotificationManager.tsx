'use client';

import { useState, useEffect } from 'react';
import { urlBase64ToUint8Array } from '@/lib/serviceWorker';
import { apiClient } from '@/lib/api';

interface PushNotificationManagerProps {
  vapidPublicKey: string;
}

export default function PushNotificationManager({ vapidPublicKey }: PushNotificationManagerProps) {
  const [isSupported, setIsSupported] = useState(false);
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
      setIsSupported(true);
      registerServiceWorker();
    }
  }, []);

  async function registerServiceWorker() {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/',
        updateViaCache: 'none',
      });
      const sub = await registration.pushManager.getSubscription();
      setSubscription(sub);
    } catch (err) {
      console.error('Service worker registration failed:', err);
    }
  }

  async function subscribeToPush() {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      console.log('🔔 Starting push notification subscription...');
      console.log('VAPID Public Key:', vapidPublicKey ? 'Present' : 'Missing');
      
      const registration = await navigator.serviceWorker.ready;
      console.log('✅ Service worker ready:', registration);
      
      const sub = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
      });
      console.log('✅ Browser subscription created:', sub);
      
      // Send subscription to backend
      const subscriptionData = {
        endpoint: sub.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(sub.getKey('p256dh')),
          auth: arrayBufferToBase64(sub.getKey('auth'))
        },
        user_agent: navigator.userAgent
      };
      
      console.log('📤 Sending subscription to backend:', subscriptionData);
      const response = await apiClient.post('/api/notifications/subscribe', subscriptionData);
      console.log('✅ Backend response:', response);
      
      setSubscription(sub);
      setSuccess('Successfully subscribed to push notifications!');
    } catch (err: any) {
      console.error('❌ Subscription error:', err);
      console.error('Error details:', {
        message: err.message,
        status: err.status,
        stack: err.stack
      });
      setError(err.message || 'Failed to subscribe to push notifications');
    } finally {
      setLoading(false);
    }
  }

  async function unsubscribeFromPush() {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      if (subscription) {
        // Unsubscribe from backend
        await apiClient.delete(`/api/notifications/unsubscribe?endpoint=${encodeURIComponent(subscription.endpoint)}`);
        
        // Unsubscribe from browser
        await subscription.unsubscribe();
        setSubscription(null);
        setSuccess('Successfully unsubscribed from push notifications!');
      }
    } catch (err: any) {
      setError(err.message || 'Failed to unsubscribe from push notifications');
      console.error('Unsubscribe error:', err);
    } finally {
      setLoading(false);
    }
  }

  async function sendTestNotification() {
    if (!message.trim()) {
      setError('Please enter a message');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      console.log('📨 Sending test notification with message:', message);
      const response = await apiClient.post('/api/notifications/test', { message });
      console.log('✅ Test notification response:', response);
      setSuccess('Test notification sent!');
      setMessage('');
    } catch (err: any) {
      console.error('❌ Test notification error:', err);
      console.error('Error details:', {
        message: err.message,
        status: err.status,
        stack: err.stack
      });
      setError(err.message || 'Failed to send test notification');
    } finally {
      setLoading(false);
    }
  }

  function arrayBufferToBase64(buffer: ArrayBuffer | null): string {
    if (!buffer) return '';
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  if (!isSupported) {
    return <p>Push notifications are not supported in this browser.</p>;
  }

  return (
    <div className="space-y-4">
      {/* Error Alert */}
      {error && (
        <div className="alert alert-error">
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Success Alert */}
      {success && (
        <div className="alert alert-success">
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{success}</span>
        </div>
      )}

      <div className="card bg-base-200">
        <div className="card-body">
          <h3 className="card-title">Push Notifications</h3>
          {subscription ? (
            <>
              <p className="text-success">✓ You are subscribed to push notifications.</p>
              <button 
                className="btn btn-error" 
                onClick={unsubscribeFromPush}
                disabled={loading}
              >
                {loading ? <span className="loading loading-spinner"></span> : 'Unsubscribe'}
              </button>
              
              <div className="divider">Test Notification</div>
              
              <input
                type="text"
                placeholder="Enter notification message"
                className="input input-bordered"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                disabled={loading}
              />
              <button 
                className="btn btn-primary" 
                onClick={sendTestNotification}
                disabled={loading || !message.trim()}
              >
                {loading ? <span className="loading loading-spinner"></span> : 'Send Test Notification'}
              </button>
            </>
          ) : (
            <>
              <p>You are not subscribed to push notifications.</p>
              <button 
                className="btn btn-primary" 
                onClick={subscribeToPush}
                disabled={loading}
              >
                {loading ? <span className="loading loading-spinner"></span> : 'Subscribe'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
