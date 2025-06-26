import { useEffect, useRef, useState, useCallback } from 'react';
import Logger from '../utils/logger';

interface WebSocketMessage {
  type: string;
  data: any;
}

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: any) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  sendMessage: (message: WebSocketMessage) => void;
  reconnect: () => void;
}

export function useWebSocket({
  url,
  onMessage,
  onError,
  onOpen,
  onClose,
  reconnectInterval = 5000,
  maxReconnectAttempts = 5,
  pingInterval = 30000,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isConnectingRef = useRef(false);
  const currentUrlRef = useRef<string>(url);

  // Store callbacks in refs to prevent unnecessary re-renders
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage;
    onErrorRef.current = onError;
    onOpenRef.current = onOpen;
    onCloseRef.current = onClose;
  }, [onMessage, onError, onOpen, onClose]);

  // Clear all timeouts
  const clearTimeouts = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (pingTimeoutRef.current) {
      clearTimeout(pingTimeoutRef.current);
      pingTimeoutRef.current = null;
    }
  }, []);

  // Send ping message
  const sendPing = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        Logger.debug('Sent ping message', 'useWebSocket', 'sendPing', 60);
      } catch (error) {
        Logger.error('Failed to send ping', 'useWebSocket', 'sendPing', 62, error);
      }
    }
  }, []);

  // Setup ping interval
  const setupPingInterval = useCallback(() => {
    clearTimeouts();
    pingTimeoutRef.current = setInterval(sendPing, pingInterval);
  }, [clearTimeouts, sendPing, pingInterval]);

  // Connect to WebSocket - now stable and doesn't depend on callbacks
  const connect = useCallback(() => {
    if (isConnectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    isConnectingRef.current = true;
    Logger.info('Connecting to WebSocket', 'useWebSocket', 'connect', 80, { url });

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        Logger.info('WebSocket connection established', 'useWebSocket', 'onopen', 87);
        setIsConnected(true);
        isConnectingRef.current = false;
        reconnectAttemptsRef.current = 0;
        setupPingInterval();
        onOpenRef.current?.();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          // Handle ping-pong
          if (data.type === 'ping') {
            // Respond to ping with pong
            ws.send(JSON.stringify({ type: 'pong', timestamp: data.timestamp }));
            Logger.debug('Responded to ping with pong', 'useWebSocket', 'onmessage', 103);
            return;
          }

          if (data.type === 'pong') {
            Logger.debug('Received pong response', 'useWebSocket', 'onmessage', 108);
            return;
          }

          // Handle other messages
          Logger.debug('Received WebSocket message', 'useWebSocket', 'onmessage', 116, data);
          onMessageRef.current?.(data);
        } catch (error) {
          Logger.error('Failed to parse WebSocket message', 'useWebSocket', 'onmessage', 121, error);
        }
      };

      ws.onerror = (error) => {
        Logger.error('WebSocket error occurred', 'useWebSocket', 'onerror', 127, error);
        isConnectingRef.current = false;
        onErrorRef.current?.(error);
      };

      ws.onclose = (event) => {
        Logger.info('WebSocket connection closed', 'useWebSocket', 'onclose', 141, {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        });

        setIsConnected(false);
        isConnectingRef.current = false;
        clearTimeouts();
        onCloseRef.current?.();

        // Attempt to reconnect if not a clean close and under max attempts
        if (!event.wasClean && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          Logger.info('Attempting to reconnect', 'useWebSocket', 'onclose', 160, {
            attempt: reconnectAttemptsRef.current,
            maxAttempts: maxReconnectAttempts
          });

          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (error) {
      Logger.error('Failed to create WebSocket connection', 'useWebSocket', 'connect', 170, error);
      isConnectingRef.current = false;
    }
  }, [url, reconnectInterval, maxReconnectAttempts, setupPingInterval, clearTimeouts]);

  // Manual reconnect function
  const reconnect = useCallback(() => {
    Logger.info('Manual reconnect requested', 'useWebSocket', 'reconnect', 175);
    if (wsRef.current) {
      wsRef.current.close();
    }
    reconnectAttemptsRef.current = 0;
    connect();
  }, [connect]);

  // Send message function
  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message));
        Logger.debug('Sent WebSocket message', 'useWebSocket', 'sendMessage', 185, message);
      } catch (error) {
        Logger.error('Failed to send WebSocket message', 'useWebSocket', 'sendMessage', 187, error);
      }
    } else {
      Logger.warn('Cannot send message - WebSocket not connected', 'useWebSocket', 'sendMessage', 191);
    }
  }, []);

  // Initialize connection and handle URL changes
  useEffect(() => {
    // If URL changed, close existing connection and reconnect
    if (currentUrlRef.current !== url) {
      Logger.info('URL changed, reconnecting WebSocket', 'useWebSocket', 'useEffect', 200, {
        oldUrl: currentUrlRef.current,
        newUrl: url
      });
      if (wsRef.current) {
        wsRef.current.close();
      }
      currentUrlRef.current = url;
    }

    // Only connect if we don't have an active connection
    if (!wsRef.current || wsRef.current.readyState === WebSocket.CLOSED) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      clearTimeouts();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [url]); // Only depend on URL changes

  return {
    isConnected,
    sendMessage,
    reconnect,
  };
}
