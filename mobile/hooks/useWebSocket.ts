import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface UseWebSocketOptions {
  url: string;
  userId: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Error) => void;
}

/**
 * React Native compatible WebSocket hook
 * Works with Expo and React Native applications
 */
export const useWebSocket = ({
  url,
  userId,
  autoConnect = true,
  reconnectAttempts = 5,
  reconnectDelay = 3000,
  onMessage,
  onConnect,
  onDisconnect,
  onError,
}: UseWebSocketOptions) => {
  const ws = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const reconnectCount = useRef(0);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const messageQueue = useRef<WebSocketMessage[]>([]);

  const connect = useCallback(async () => {
    if (isConnected || isConnecting || !url) return;

    setIsConnecting(true);
    try {
      const fullUrl = `${url}?user_id=${userId}`;
      ws.current = new WebSocket(fullUrl);

      ws.current.onopen = () => {
        console.log('[WebSocket] Connected');
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        reconnectCount.current = 0;

        // Send queued messages
        while (messageQueue.current.length > 0) {
          const message = messageQueue.current.shift();
          if (message && ws.current) {
            ws.current.send(JSON.stringify(message));
          }
        }

        onConnect?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage;
          onMessage?.(message);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.current.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        const wsError = new Error('WebSocket error');
        setError(wsError);
        onError?.(wsError);
      };

      ws.current.onclose = () => {
        console.log('[WebSocket] Disconnected');
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnect?.();

        // Attempt reconnection
        if (reconnectCount.current < reconnectAttempts) {
          reconnectCount.current++;
          const delay = reconnectDelay * reconnectCount.current;
          console.log(`[WebSocket] Reconnecting in ${delay}ms...`);
          reconnectTimeout.current = setTimeout(() => {
            connect();
          }, delay);
        }
      };
    } catch (error) {
      const wsError = error instanceof Error ? error : new Error('Connection failed');
      setError(wsError);
      setIsConnecting(false);
      onError?.(wsError);
    }
  }, [url, userId, isConnected, isConnecting, onConnect, onDisconnect, onError, onMessage, reconnectAttempts, reconnectDelay]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const send = useCallback(
    (message: WebSocketMessage) => {
      if (ws.current && isConnected) {
        try {
          ws.current.send(JSON.stringify(message));
        } catch (error) {
          console.error('[WebSocket] Failed to send message:', error);
          messageQueue.current.push(message);
        }
      } else {
        // Queue message for later sending
        messageQueue.current.push(message);
        if (!isConnecting && !isConnected) {
          connect();
        }
      }
    },
    [isConnected, isConnecting, connect]
  );

  const ping = useCallback(() => {
    send({ type: 'ping', timestamp: Date.now() });
  }, [send]);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    error,
    send,
    ping,
    connect,
    disconnect,
  };
};

/**
 * Hook for project WebSocket room (Mobile)
 */
export const useProjectWebSocket = (
  projectId: string,
  userId: string,
  handlers?: {
    onTaskCreated?: (task: any) => void;
    onTaskUpdated?: (task: any) => void;
    onTaskDeleted?: (taskId: string) => void;
    onTaskStatusUpdated?: (task: any) => void;
    onProjectUpdated?: (project: any) => void;
    onUserJoined?: (users: string[]) => void;
    onUserLeft?: (count: number) => void;
  }
) => {
  const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'task_created':
        handlers?.onTaskCreated?.(message.task);
        break;
      case 'task_updated':
        handlers?.onTaskUpdated?.(message.task);
        break;
      case 'task_deleted':
        handlers?.onTaskDeleted?.(message.task_id);
        break;
      case 'task_status_updated':
        handlers?.onTaskStatusUpdated?.(message.task);
        break;
      case 'project_updated':
        handlers?.onProjectUpdated?.(message.project);
        break;
      case 'user_joined':
        handlers?.onUserJoined?.(message.active_users);
        break;
      case 'user_left':
        handlers?.onUserLeft?.(message.active_count);
        break;
    }
  };

  return useWebSocket({
    url: `${wsUrl}/ws/project/${projectId}`,
    userId,
    onMessage: handleMessage,
  });
};

/**
 * Hook for agent execution WebSocket room (Mobile)
 */
export const useAgentWebSocket = (
  agentId: string,
  userId: string,
  handlers?: {
    onExecutionUpdate?: (data: any) => void;
    onExecutionComplete?: (data: any) => void;
  }
) => {
  const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'execution_update':
        handlers?.onExecutionUpdate?.(message);
        break;
      case 'execution_complete':
        handlers?.onExecutionComplete?.(message);
        break;
    }
  };

  return useWebSocket({
    url: `${wsUrl}/ws/agent/${agentId}`,
    userId,
    onMessage: handleMessage,
  });
};

/**
 * Hook for notifications WebSocket room (Mobile)
 */
export const useNotificationsWebSocket = (
  userId: string,
  handlers?: {
    onNotification?: (notification: any) => void;
  }
) => {
  const apiUrl = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
  const wsUrl = apiUrl.replace('http://', 'ws://').replace('https://', 'wss://');

  const handleMessage = (message: any) => {
    if (message.type === 'notification') {
      handlers?.onNotification?.(message);
    }
  };

  return useWebSocket({
    url: `${wsUrl}/ws/notifications`,
    userId,
    onMessage: handleMessage,
  });
};
