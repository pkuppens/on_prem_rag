import React, { useState } from 'react';
import { Container, Typography, Paper, Box, Button, Alert, Chip } from '@mui/material';
import { useWebSocket } from '../hooks/useWebSocket';
import { apiUrls } from '../config/api';
import Logger from '../utils/logger';

export const WebSocketTestPage = () => {
  const [messages, setMessages] = useState<string[]>([]);
  const [connectionCount, setConnectionCount] = useState(0);

  const { isConnected, sendMessage, reconnect } = useWebSocket({
    url: apiUrls.uploadProgressWebSocket(),
    onMessage: (data) => {
      setMessages(prev => [...prev, `Received: ${JSON.stringify(data)}`]);
    },
    onError: (error) => {
      setMessages(prev => [...prev, `Error: ${error}`]);
    },
    onOpen: () => {
      setConnectionCount(prev => prev + 1);
      setMessages(prev => [...prev, 'Connected']);
    },
    onClose: () => {
      setMessages(prev => [...prev, 'Disconnected']);
    },
  });

  const sendTestMessage = () => {
    sendMessage({ type: 'test', data: 'Hello from frontend!' });
    setMessages(prev => [...prev, 'Sent test message']);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        WebSocket Test Page
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Connection Status
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2 }}>
          <Chip
            label={isConnected ? 'Connected' : 'Disconnected'}
            color={isConnected ? 'success' : 'error'}
          />
          <Typography>Connections: {connectionCount}</Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button onClick={sendTestMessage} disabled={!isConnected}>
            Send Test Message
          </Button>
          <Button onClick={reconnect}>
            Reconnect
          </Button>
        </Box>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Messages ({messages.length})
        </Typography>
        <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
          {messages.map((msg, index) => (
            <Typography key={index} variant="body2" sx={{ mb: 1 }}>
              {msg}
            </Typography>
          ))}
        </Box>
      </Paper>
    </Container>
  );
};
