'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { useProjectWebSocket, useAgentWebSocket, useNotificationsWebSocket } from '@/hooks/useWebSocket';

interface WebSocketContextType {
  projectWebSocket: {
    connect: (projectId: string, userId: string) => void;
    disconnect: () => void;
    send: (message: any) => void;
    isConnected: boolean;
  };
  agentWebSocket: {
    connect: (agentId: string, userId: string) => void;
    disconnect: () => void;
    send: (message: any) => void;
    isConnected: boolean;
  };
  notificationsWebSocket: {
    disconnect: () => void;
    send: (message: any) => void;
    isConnected: boolean;
  };
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider = ({ children }: { children: ReactNode }) => {
  // Implementation will manage WebSocket connections
  // This is a placeholder for context structure

  return (
    <WebSocketContext.Provider value={undefined as any}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within WebSocketProvider');
  }
  return context;
};
