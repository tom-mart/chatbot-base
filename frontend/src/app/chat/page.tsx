'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useToast } from '@/contexts/ToastContext';
import { apiClient } from '@/lib/api';
import ChatbotLogo from '@/components/ChatbotLogo';
import MarkdownMessage from '@/components/MarkdownMessage';
import PWAInstallPrompt from '@/components/PWAInstallPrompt';
import NewSessionModal, { SessionConfig } from '@/components/NewSessionModal';

interface Message {
  id: string;
  role: 'human' | 'ai' | 'system';
  content: string;
  created_at: string;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  model: string;
  first_message?: string;
}

export default function ChatPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const { theme, setTheme, themeConfig } = useTheme();
  const { showToast } = useToast();
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showNewSessionModal, setShowNewSessionModal] = useState(false);
  const [pendingSessionConfig, setPendingSessionConfig] = useState<SessionConfig | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingMessageRef = useRef<string>('');
  const lastActivityRef = useRef<number>(Date.now());
  const inactivityCheckIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Inactivity check - redirect to login after 15 minutes of inactivity
  useEffect(() => {
    const INACTIVITY_TIMEOUT = 15 * 60 * 1000; // 15 minutes in milliseconds

    const checkInactivity = () => {
      const now = Date.now();
      const timeSinceLastActivity = now - lastActivityRef.current;
      
      if (timeSinceLastActivity >= INACTIVITY_TIMEOUT) {
        showToast('Session expired due to inactivity', 'warning');
        logout();
      }
    };

    // Update last activity on user interactions
    const updateActivity = () => {
      lastActivityRef.current = Date.now();
    };

    // Track various user activities
    window.addEventListener('mousedown', updateActivity);
    window.addEventListener('keydown', updateActivity);
    window.addEventListener('touchstart', updateActivity);
    window.addEventListener('scroll', updateActivity);

    // Check for inactivity every minute
    inactivityCheckIntervalRef.current = setInterval(checkInactivity, 60 * 1000);

    // Cleanup
    return () => {
      window.removeEventListener('mousedown', updateActivity);
      window.removeEventListener('keydown', updateActivity);
      window.removeEventListener('touchstart', updateActivity);
      window.removeEventListener('scroll', updateActivity);
      if (inactivityCheckIntervalRef.current) {
        clearInterval(inactivityCheckIntervalRef.current);
      }
    };
  }, [logout, showToast]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSessions = async () => {
    try {
      const data = await apiClient.get<Session[]>('/api/langchain-chat/sessions');
      setSessions(data);
    } catch (error: any) {
      console.error('Failed to load sessions:', error);
      showToast(error.message || 'Failed to load sessions', 'error');
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const data = await apiClient.get<Message[]>(`/api/langchain-chat/sessions/${sessionId}/messages`);
      // Filter out system messages (role: 'system')
      const userMessages = data.filter(msg => msg.role !== 'system');
      // Sort by created_at to ensure chronological order
      const sortedMessages = userMessages.sort((a, b) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );
      setMessages(sortedMessages);
      setCurrentSessionId(sessionId);
      setSidebarOpen(false);
      lastActivityRef.current = Date.now();
    } catch (error: any) {
      console.error('Failed to load session:', error);
      showToast(error.message || 'Failed to load session', 'error');
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await apiClient.delete(`/api/langchain-chat/sessions/${sessionId}`);
      if (currentSessionId === sessionId) {
        setMessages([]);
        setCurrentSessionId(null);
      }
      showToast('Session deleted successfully', 'success');
      loadSessions();
    } catch (error: any) {
      console.error('Failed to delete session:', error);
      showToast(error.message || 'Failed to delete session', 'error');
    }
  };

  const handleNewSessionChoice = (config?: SessionConfig) => {
    // Don't create session yet, just store the config and close modal
    const sessionConfig = config || {
      title: 'New Conversation',
      system_prompt: 'You are a helpful AI assistant.',
      model: 'qwen2.5:latest',
      temperature: 0.8,
      num_ctx: 8192,
    };
    setPendingSessionConfig(sessionConfig);
    setCurrentSessionId(null);
    setMessages([]);
    setShowNewSessionModal(false);
    setSidebarOpen(false);
    lastActivityRef.current = Date.now();
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message to UI immediately
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'human',
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);
    lastActivityRef.current = Date.now();

    // Create session if none exists (auto-create on first message)
    let sessionId = currentSessionId;
    if (!sessionId) {
      try {
        // Use pending config if available, otherwise use defaults
        const config = pendingSessionConfig || {
          title: 'New Conversation',
          system_prompt: 'You are a helpful AI assistant.',
          model: 'qwen2.5:latest',
          temperature: 0.8,
          num_ctx: 8192,
        };
        
        const session = await apiClient.post<Session>('/api/langchain-chat/sessions', config);
        sessionId = session.id;
        setCurrentSessionId(session.id);
        setPendingSessionConfig(null); // Clear pending config
        loadSessions();
      } catch (error: any) {
        console.error('Failed to create session:', error);
        showToast(error.message || 'Failed to create session', 'error');
        setMessages((prev) => prev.slice(0, -1)); // Remove the user message
        return;
      }
    }

    setIsStreaming(true);
    streamingMessageRef.current = '';

    // Add placeholder for AI response
    setMessages((prev) => [...prev, {
      id: `temp-assistant-${Date.now()}`,
      role: 'ai',
      content: '',
      created_at: new Date().toISOString(),
    }]);

    try {
      const stream = await apiClient.streamPost(
        `/api/langchain-chat/sessions/${sessionId}/chat/stream`,
        { message: userMessage }
      );

      const reader = stream.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;
        
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;
          
          try {
            const data = JSON.parse(line.slice(6));

            if (data.type === 'content') {
              streamingMessageRef.current += data.content;
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage && lastMessage.role === 'ai') {
                  lastMessage.content = streamingMessageRef.current;
                }
                return newMessages;
              });
            } else if (data.type === 'end') {
              setMessages((prev) => {
                const newMessages = [...prev];
                const lastMessage = newMessages[newMessages.length - 1];
                if (lastMessage && lastMessage.role === 'ai') {
                  lastMessage.id = data.message.id;
                  lastMessage.content = data.message.content;
                  lastMessage.created_at = data.message.created_at;
                }
                return newMessages;
              });
              loadSessions();
            } else if (data.type === 'error') {
              console.error('Streaming error:', data.message);
            }
          } catch (error) {
            console.error('Failed to parse streaming data:', error);
          }
        }
      }
    } catch (error: any) {
      console.error('Failed to send message:', error);
      showToast(error.message || 'Failed to send message', 'error');
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.role === 'ai') {
          lastMessage.content = 'Sorry, I encountered an error. Please try again.';
        }
        return newMessages;
      });
    } finally {
      setIsStreaming(false);
      streamingMessageRef.current = '';
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
    <div className="flex h-screen overflow-hidden bg-base-200">
      <PWAInstallPrompt />
      <NewSessionModal
        isOpen={showNewSessionModal}
        onClose={() => setShowNewSessionModal(false)}
        onCreateDefault={() => handleNewSessionChoice()}
        onCreateCustom={(config) => handleNewSessionChoice(config)}
      />

      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:relative z-30 w-80 h-full bg-base-100 shadow-xl transition-transform duration-300 ease-in-out flex flex-col border-r border-base-200`}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-6 border-b border-base-200 bg-gradient-to-r from-primary/5 to-secondary/5">
          <div className="flex items-center space-x-3">
            <ChatbotLogo size="md" variant="gradient" />
            <div>
              <h1 className="font-bold text-lg text-base-content">Chatbot</h1>
              <p className="text-xs text-base-content/60">AI Assistant</p>
            </div>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden btn btn-ghost btn-sm btn-circle hover:bg-base-200"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button onClick={() => setShowNewSessionModal(true)} className="btn btn-primary w-full gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Chat
          </button>
        </div>

        {/* Sidebar Content */}
        <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-2">
          {/* Navigation Links */}
          <div className="space-y-1">
            <button
              onClick={() => router.push('/files')}
              className="btn btn-ghost w-full justify-start gap-2 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              My Files
            </button>
            <button
              onClick={() => router.push('/settings')}
              className="btn btn-ghost w-full justify-start gap-2 text-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Settings
            </button>
          </div>

          <div className="divider my-2"></div>

          {/* Chat History - Collapsed by default */}
          <details className="collapse collapse-arrow bg-base-200/50 rounded-box">
            <summary className="collapse-title text-sm font-semibold text-base-content/70 uppercase tracking-wide min-h-0 py-3">
              Chat History
            </summary>
            <div className="collapse-content px-2">
              <div className="space-y-2 mt-2">
                {sessions.length === 0 ? (
                  <div className="text-center py-6 text-base-content/50">
                    <svg className="w-10 h-10 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                    </svg>
                    <p className="text-xs">No sessions yet</p>
                  </div>
                ) : (
                  sessions.map((session) => (
                    <div
                      key={session.id}
                      className={`group relative p-3 rounded-xl cursor-pointer transition-all duration-200 ${
                        currentSessionId === session.id 
                          ? 'bg-primary/10 border border-primary/20 shadow-sm' 
                          : 'hover:bg-base-200/70 hover:shadow-sm'
                      }`}
                      onClick={() => loadSession(session.id)}
                    >
                      <div className="pr-8">
                        <div className="font-medium text-sm truncate mb-1">
                          {session.first_message || session.title}
                        </div>
                        <div className="text-xs text-base-content/50">
                          {new Date(session.updated_at).toLocaleDateString(undefined, { 
                            month: 'short', 
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm('Delete this session?')) {
                            deleteSession(session.id);
                          }
                        }}
                        className="absolute right-2 top-1/2 transform -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-error/20 rounded-lg"
                        title="Delete session"
                      >
                        <svg className="w-3.5 h-3.5 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          </details>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-base-200 space-y-2">
          <button 
            onClick={logout}
            className="btn btn-ghost w-full justify-start gap-2 text-error"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        {/* Mobile Header with Breadcrumbs */}
        <div className="lg:hidden sticky top-0 z-10 bg-base-100/95 backdrop-blur-sm border-b border-base-200 shadow-sm">
          <div className="flex items-center justify-between p-3">
            <button 
              onClick={() => setSidebarOpen(true)}
              className="btn btn-ghost btn-sm btn-circle"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <div className="flex items-center space-x-2">
              <ChatbotLogo size="sm" variant="simple" />
              <span className="font-semibold text-base">Chatbot</span>
            </div>
            <div className="dropdown dropdown-end">
              <label tabIndex={0} className="btn btn-ghost btn-sm btn-circle">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                </svg>
              </label>
            <ul tabIndex={0} className="dropdown-content z-[100] menu p-2 bg-base-100 border border-base-300 rounded-box w-64 shadow-2xl mt-2 max-h-[70vh] overflow-y-auto">
              <li className="menu-title">
                <span className="text-xs font-semibold uppercase tracking-wider">Choose Theme</span>
              </li>
              {themeConfig.map((t) => (
                <li key={t.name}>
                  <button
                    className={`flex items-center gap-3 py-3 ${theme === t.name ? 'active bg-primary/10' : ''}`}
                    onClick={() => setTheme(t.name as any)}
                  >
                    <span className="text-2xl">{t.icon}</span>
                    <div className="flex-1 text-left">
                      <div className="font-medium capitalize">{t.name}</div>
                      <div className="text-xs text-base-content/60">{t.description}</div>
                    </div>
                    {theme === t.name && (
                      <svg className="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                </li>
              ))}
            </ul>
            </div>
          </div>
          {/* Mobile Breadcrumbs */}
          <div className="px-3 pb-2">
            <div className="text-xs breadcrumbs">
              <ul>
                <li>
                  <button onClick={() => router.push('/home')} className="hover:text-primary">
                    Home
                  </button>
                </li>
                <li>Chat</li>
                {currentSessionId && (
                  <li className="text-base-content/60 truncate max-w-[120px]">
                    {sessions.find(s => s.id === currentSessionId)?.title || 'Session'}
                  </li>
                )}
              </ul>
            </div>
          </div>
        </div>

        {/* Desktop Header with Breadcrumbs */}
        <div className="hidden lg:flex items-center justify-between p-4 bg-base-100 border-b border-base-200">
          <div className="flex items-center space-x-2">
            {/* Breadcrumb Navigation */}
            <div className="text-sm breadcrumbs">
              <ul>
                <li>
                  <button onClick={() => router.push('/home')} className="hover:text-primary">
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                    Home
                  </button>
                </li>
                <li>
                  <span className="font-semibold">Chat</span>
                </li>
                {currentSessionId && (
                  <li>
                    <span className="text-base-content/60">
                      {sessions.find(s => s.id === currentSessionId)?.title || 'Session'}
                    </span>
                  </li>
                )}
              </ul>
            </div>
          </div>
          <div className="dropdown dropdown-end">
            <label tabIndex={0} className="btn btn-ghost btn-sm gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
              </svg>
              <span className="hidden xl:inline">Theme</span>
            </label>
            <ul tabIndex={0} className="dropdown-content z-[100] menu p-2 bg-base-100 border border-base-300 rounded-box w-64 shadow-2xl mt-2 max-h-[70vh] overflow-y-auto">
              <li className="menu-title">
                <span className="text-xs font-semibold uppercase tracking-wider">Choose Theme</span>
              </li>
              {themeConfig.map((t) => (
                <li key={t.name}>
                  <button
                    className={`flex items-center gap-3 py-3 ${theme === t.name ? 'active bg-primary/10' : ''}`}
                    onClick={() => setTheme(t.name as any)}
                  >
                    <span className="text-2xl">{t.icon}</span>
                    <div className="flex-1 text-left">
                      <div className="font-medium capitalize">{t.name}</div>
                      <div className="text-xs text-base-content/60">{t.description}</div>
                    </div>
                    {theme === t.name && (
                      <svg className="w-4 h-4 text-primary" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <ChatbotLogo size="4xl" />
              <h2 className="text-2xl font-bold mt-6 mb-2">Welcome to Chatbot</h2>
              <p className="text-base-content/60 mb-6">Start a conversation or create a new session</p>
              <button onClick={() => setShowNewSessionModal(true)} className="btn btn-primary gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Chat
              </button>
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'human' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    message.role === 'human'
                      ? 'bg-primary text-primary-content'
                      : 'bg-base-300 text-base-content'
                  }`}
                >
                  <MarkdownMessage content={message.content} isUser={message.role === 'human'} />
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="border-t border-base-200 p-4 bg-base-100">
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              placeholder="Type your message..."
              className="input input-bordered flex-1"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isStreaming}
            />
            <button
              type="submit"
              className={`btn btn-primary ${isStreaming ? 'loading' : ''}`}
              disabled={isStreaming || !input.trim()}
            >
              {!isStreaming && (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
