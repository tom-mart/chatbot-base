'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import PushNotificationManager from '@/components/PushNotificationManager';
import { apiClient } from '@/lib/api';

export default function SettingsPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [vapidPublicKey, setVapidPublicKey] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadVapidKey();
    }
  }, [user]);

  const loadVapidKey = async () => {
    try {
      const data = await apiClient.get<{ public_key: string }>('/api/notifications/vapid-public-key');
      setVapidPublicKey(data.public_key);
    } catch (error) {
      console.error('Failed to load VAPID key:', error);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-base-200">
      {/* Header */}
      <div className="bg-base-100 border-b border-base-300">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-base-content">Settings</h1>
              <p className="text-base-content/60 mt-1">Manage your account and preferences</p>
            </div>
            <button
              onClick={() => router.push('/home')}
              className="btn btn-ghost btn-sm gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* User Info */}
          <div className="card bg-base-100 shadow-md">
            <div className="card-body">
              <h2 className="card-title">Account Information</h2>
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Username:</span> {user.username}
                </div>
                {user.email && (
                  <div>
                    <span className="font-medium">Email:</span> {user.email}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="card bg-base-100 shadow-md">
            <div className="card-body">
              <h2 className="card-title">Quick Links</h2>
              <div className="flex flex-col gap-2">
                <button
                  onClick={() => router.push('/files')}
                  className="btn btn-outline justify-start gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  My Files
                </button>
                <button
                  onClick={() => router.push('/chat')}
                  className="btn btn-outline justify-start gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                  Chat
                </button>
              </div>
            </div>
          </div>

          {/* Push Notifications */}
          {loading ? (
            <div className="card bg-base-100 shadow-md">
              <div className="card-body">
                <div className="flex items-center justify-center py-8">
                  <span className="loading loading-spinner loading-lg text-primary"></span>
                </div>
              </div>
            </div>
          ) : vapidPublicKey ? (
            <PushNotificationManager vapidPublicKey={vapidPublicKey} />
          ) : (
            <div className="card bg-base-100 shadow-md">
              <div className="card-body">
                <h2 className="card-title">Push Notifications</h2>
                <p className="text-error">Push notifications are not configured on the server.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
