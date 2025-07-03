# WebSocket Connection Improvements

## Problem

The original WebSocket implementation had several issues:

1. **Connection instability**: WebSocket connections were being closed prematurely
2. **No ping-pong mechanism**: No heartbeat to keep connections alive
3. **Manual connection management**: Each component managed its own WebSocket connection
4. **Inconsistent error handling**: Different error handling across components

## Solution

### 1. Custom WebSocket Hook (`useWebSocket`)

Created a robust custom React hook that provides:

- **Persistent connections**: Automatic reconnection with configurable retry logic
- **Ping-pong heartbeat**: Sends ping messages every 30 seconds to keep connections alive
- **Centralized management**: Single hook used across all components
- **Error handling**: Comprehensive error handling and logging
- **Connection state**: Real-time connection status tracking

### 2. Backend WebSocket Handler Updates

Enhanced the backend WebSocket handler to support:

- **Dual ping-pong formats**: Both string (`"ping"`/`"pong"`) and JSON (`{"type": "ping"}`/`{"type": "pong"}`)
- **Better error handling**: Improved error logging and connection cleanup
- **Message validation**: Proper handling of different message types

### 3. Component Updates

Updated all components to use the new WebSocket hook:

- **App.tsx**: Main application component
- **PDFTestPage.tsx**: PDF testing page
- **UploadPage.tsx**: File upload page

## Implementation Details

### Frontend Hook (`src/frontend/src/hooks/useWebSocket.ts`)

```typescript
const { isConnected, sendMessage, reconnect } = useWebSocket({
  url: apiUrls.uploadProgressWebSocket(),
  onMessage: (data) => {
    /* handle progress updates */
  },
  onError: (error) => {
    /* handle errors */
  },
  onOpen: () => {
    /* connection established */
  },
  onClose: () => {
    /* connection closed */
  },
  reconnectInterval: 5000, // 5 seconds between reconnection attempts
  maxReconnectAttempts: 5, // Maximum 5 reconnection attempts
  pingInterval: 30000, // Send ping every 30 seconds
});
```

### Backend Handler (`src/backend/rag_pipeline/api/websocket.py`)

The backend now handles both ping formats:

```python
# String ping/pong (legacy support)
if message == "ping":
    await websocket.send_text("pong")

# JSON ping/pong (new format)
elif json_data.get("type") == "ping":
    pong_response = {
        "type": "pong",
        "timestamp": json_data.get("timestamp")
    }
    await websocket.send_text(json.dumps(pong_response))
```

## Benefits

1. **Reliable connections**: Persistent WebSocket connections with automatic reconnection
2. **Better user experience**: Real-time progress updates without connection drops
3. **Maintainable code**: Centralized WebSocket management
4. **Robust error handling**: Comprehensive error handling and logging
5. **Backward compatibility**: Supports both old and new ping-pong formats

## Testing

Use the test script to verify WebSocket functionality:

```bash
python tests/test_websocket_connection.py
```

This script tests:

- String ping/pong functionality
- JSON ping/pong functionality
- Connection stability with multiple pings
- Error handling

## Configuration

The WebSocket hook can be configured with these options:

- `reconnectInterval`: Time between reconnection attempts (default: 5000ms)
- `maxReconnectAttempts`: Maximum number of reconnection attempts (default: 5)
- `pingInterval`: Time between ping messages (default: 30000ms)

## Migration Guide

To migrate existing components to use the new WebSocket hook:

1. Import the hook: `import { useWebSocket } from '../hooks/useWebSocket';`
2. Replace manual WebSocket setup with the hook
3. Remove manual ping interval management
4. Update event handlers to use the hook's callbacks

Example migration:

```typescript
// Before (manual WebSocket)
const [ws, setWs] = useState<WebSocket | null>(null);
useEffect(() => {
  const websocket = new WebSocket(url);
  // ... manual setup
}, []);

// After (using hook)
const { isConnected } = useWebSocket({
  url,
  onMessage: (data) => {
    /* handle messages */
  },
  // ... other callbacks
});
```
