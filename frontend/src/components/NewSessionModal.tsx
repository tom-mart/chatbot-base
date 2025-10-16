'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';

interface NewSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreateDefault: () => void;
  onCreateCustom: (config: SessionConfig) => void;
}

export interface SessionConfig {
  title: string;
  model: string;
  system_prompt: string;
  temperature?: number;
  top_k?: number;
  top_p?: number;
  num_ctx?: number;
  max_tokens?: number;
}

export default function NewSessionModal({ isOpen, onClose, onCreateDefault, onCreateCustom }: NewSessionModalProps) {
  const [mode, setMode] = useState<'choice' | 'custom'>('choice');
  const [models, setModels] = useState<Array<{ name: string }>>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [config, setConfig] = useState<SessionConfig>({
    title: 'New Conversation',
    model: 'qwen2.5:latest',
    system_prompt: 'You are a helpful AI assistant.',
    temperature: 0.8,
    num_ctx: 8192,
  });

  useEffect(() => {
    if (isOpen) {
      loadModels();
    }
  }, [isOpen]);

  const loadModels = async () => {
    setLoadingModels(true);
    try {
      const response = await apiClient.get<{ models: Array<{ name: string }> }>('/api/langchain-chat/models');
      setModels(response.models || []);
      // Set first model as default if available
      if (response.models && response.models.length > 0) {
        setConfig(prev => ({ ...prev, model: response.models[0].name }));
      }
    } catch (error) {
      console.error('Failed to load models:', error);
      // Fallback to hardcoded models
      setModels([
        { name: 'qwen2.5:latest' },
        { name: 'llama3.2:latest' },
        { name: 'mistral:latest' },
        { name: 'phi3:latest' },
      ]);
    } finally {
      setLoadingModels(false);
    }
  };

  const handleCreateCustom = () => {
    onCreateCustom(config);
    setMode('choice');
    setConfig({
      title: 'New Conversation',
      model: 'qwen2.5:latest',
      system_prompt: 'You are a helpful AI assistant.',
      temperature: 0.8,
      num_ctx: 8192,
    });
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box max-w-2xl">
        {mode === 'choice' ? (
          <>
            <h3 className="font-bold text-lg mb-4">Start New Chat</h3>
            <p className="text-sm text-base-content/70 mb-6">Choose how you want to start your conversation</p>
            
            <div className="alert alert-info mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="stroke-current shrink-0 w-6 h-6">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <span className="text-sm">Session will be created when you send your first message</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => {
                  onCreateDefault();
                  onClose();
                }}
                className="btn btn-primary btn-lg h-auto py-6 flex-col gap-2"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <div>
                  <div className="font-bold">Quick Start</div>
                  <div className="text-xs opacity-70">Use default settings</div>
                </div>
              </button>

              <button
                onClick={() => setMode('custom')}
                className="btn btn-outline btn-lg h-auto py-6 flex-col gap-2"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                <div>
                  <div className="font-bold">Customize</div>
                  <div className="text-xs opacity-70">Configure all settings</div>
                </div>
              </button>
            </div>

            <div className="modal-action">
              <button onClick={onClose} className="btn">Cancel</button>
            </div>
          </>
        ) : (
          <>
            <h3 className="font-bold text-lg mb-4">Customize Chat Session</h3>
            
            <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Title</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered"
                  value={config.title}
                  onChange={(e) => setConfig({ ...config, title: e.target.value })}
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Model</span>
                </label>
                <select
                  className="select select-bordered"
                  value={config.model}
                  onChange={(e) => setConfig({ ...config, model: e.target.value })}
                  disabled={loadingModels}
                >
                  {loadingModels ? (
                    <option>Loading models...</option>
                  ) : models.length > 0 ? (
                    models.map((model) => (
                      <option key={model.name} value={model.name}>
                        {model.name}
                      </option>
                    ))
                  ) : (
                    <option value="qwen2.5:latest">No models available</option>
                  )}
                </select>
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">System Prompt</span>
                </label>
                <textarea
                  className="textarea textarea-bordered h-24"
                  value={config.system_prompt}
                  onChange={(e) => setConfig({ ...config, system_prompt: e.target.value })}
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Temperature: {config.temperature}</span>
                </label>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.1"
                  className="range range-primary"
                  value={config.temperature}
                  onChange={(e) => setConfig({ ...config, temperature: parseFloat(e.target.value) })}
                />
                <div className="w-full flex justify-between text-xs px-2 mt-1">
                  <span>Precise</span>
                  <span>Creative</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Context Window</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered"
                    value={config.num_ctx}
                    onChange={(e) => setConfig({ ...config, num_ctx: parseInt(e.target.value) })}
                  />
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text">Max Tokens</span>
                  </label>
                  <input
                    type="number"
                    className="input input-bordered"
                    value={config.max_tokens || ''}
                    onChange={(e) => setConfig({ ...config, max_tokens: e.target.value ? parseInt(e.target.value) : undefined })}
                  />
                </div>
              </div>

              <details className="collapse collapse-arrow bg-base-200">
                <summary className="collapse-title text-sm font-medium">Advanced Settings</summary>
                <div className="collapse-content space-y-4">
                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Top K</span>
                    </label>
                    <input
                      type="number"
                      className="input input-bordered input-sm"
                      value={config.top_k || ''}
                      onChange={(e) => setConfig({ ...config, top_k: e.target.value ? parseInt(e.target.value) : undefined })}
                    />
                  </div>

                  <div className="form-control">
                    <label className="label">
                      <span className="label-text">Top P</span>
                    </label>
                    <input
                      type="number"
                      step="0.1"
                      min="0"
                      max="1"
                      className="input input-bordered input-sm"
                      value={config.top_p || ''}
                      onChange={(e) => setConfig({ ...config, top_p: e.target.value ? parseFloat(e.target.value) : undefined })}
                    />
                  </div>
                </div>
              </details>
            </div>

            <div className="modal-action">
              <button onClick={() => setMode('choice')} className="btn">Back</button>
              <button onClick={handleCreateCustom} className="btn btn-primary">Create Session</button>
            </div>
          </>
        )}
      </div>
      <div className="modal-backdrop" onClick={onClose}></div>
    </div>
  );
}
