'use client';

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAuthStore } from '@/store/auth';
import { AlertCircle, Check, Zap } from 'lucide-react';

export const WebSocketStatus: React.FC<{ showDetails?: boolean }> = ({
  showDetails = false,
}) => {
  const { user } = useAuthStore();
  const [messageCount, setMessageCount] = useState(0);
  const [wsStats, setWsStats] = useState<any>(null);

  const { isConnected, isConnecting, error, send } = useWebSocket({
    url: `${process.env.NEXT_PUBLIC_API_URL?.replace('http', 'ws')}/ws/notifications`,
    userId: user?.id || '',
    autoConnect: false, // We'll connect manually to avoid spam
    onMessage: (msg) => {
      setMessageCount((prev) => prev + 1);
    },
  });

  const fetchWebSocketStats = async () => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/ws/stats`
      );
      const data = await response.json();
      setWsStats(data);
    } catch (error) {
      console.error('Failed to fetch WebSocket stats:', error);
    }
  };

  useEffect(() => {
    fetchWebSocketStats();
    const interval = setInterval(fetchWebSocketStats, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-medium text-slate-200">Real-time Status</h3>
        <div className="flex items-center gap-2">
          <div
            className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-slate-300">
            {isConnecting ? 'Connecting...' : isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-2 bg-red-900/20 rounded border border-red-700 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error.message}
        </div>
      )}

      {showDetails && (
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-slate-400">Messages received:</span>
            <span className="text-slate-200 font-mono">{messageCount}</span>
          </div>

          {wsStats && (
            <>
              <div className="flex justify-between">
                <span className="text-slate-400">Active rooms:</span>
                <span className="text-slate-200 font-mono">
                  {Object.keys(wsStats.rooms || {}).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Active connections:</span>
                <span className="text-slate-200 font-mono">
                  {wsStats.total_connections || 0}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Active users:</span>
                <span className="text-slate-200 font-mono">
                  {wsStats.total_users || 0}
                </span>
              </div>
            </>
          )}
        </div>
      )}

      <div className="flex items-center gap-2 p-2 bg-blue-900/20 rounded text-blue-400 text-xs">
        <Zap className="w-4 h-4" />
        <span>Real-time features enabled</span>
      </div>
    </div>
  );
};
