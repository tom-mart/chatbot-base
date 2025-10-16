'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import ChatbotLogo from '@/components/ChatbotLogo';

export default function HomePage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      if (user) {
        router.push('/home');
      } else {
        router.push('/login');
      }
    }
  }, [user, loading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary/10 via-base-100 to-secondary/10">
      <div className="text-center">
        <div className="mb-4">
          <ChatbotLogo size="4xl" pulse={true} />
        </div>
        <div>
          <span className="loading loading-spinner loading-lg text-primary"></span>
        </div>
      </div>
    </div>
  );
}
