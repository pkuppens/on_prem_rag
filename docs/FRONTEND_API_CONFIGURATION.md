# Frontend API Configuration System

## Overview

The frontend now uses a centralized, configurable API system that eliminates hardcoded URLs and provides environment-specific configuration. This makes the application production-ready and easier to maintain.

## Configuration Files

### 1. API Configuration (`src/frontend/src/config/api.ts`)

The main configuration module that provides:

- Environment detection (development vs production)
- Centralized API endpoint definitions
- URL builder utilities
- Configuration management

### 2. Environment Variables (`src/frontend/env.example`)

Template for environment-specific configuration:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8000
VITE_API_TIMEOUT=30000
VITE_API_DEBUG=true
```

## Key Features

### 1. Environment-Aware Configuration

The system automatically detects the environment and applies appropriate settings:

**Development (default):**

- Base URL: `http://localhost:8000`
- WebSocket: `ws://localhost:8000`
- Debug logging: Enabled
- Timeout: 30 seconds

**Production:**

- Base URL: `https://api.yourdomain.com` (configurable)
- WebSocket: `wss://api.yourdomain.com` (configurable)
- Debug logging: Disabled
- Timeout: 60 seconds

### 2. Centralized Endpoint Definitions

All API endpoints are defined in one place:

```typescript
export const API_ENDPOINTS = {
  DOCUMENTS: {
    UPLOAD: "/api/documents/upload",
    LIST: "/api/documents/list",
    FILES: "/api/documents/files",
  },
  QUERY: {
    SEARCH: "/api/query",
  },
  PARAMETERS: {
    LIST: "/api/parameters",
  },
  HEALTH: {
    STATUS: "/api/health",
  },
  WEBSOCKET: {
    UPLOAD_PROGRESS: "/ws/upload-progress",
  },
} as const;
```

### 3. URL Builder Utilities

The `ApiUrlBuilder` class provides methods for constructing URLs:

```typescript
// File serving URLs
const fileUrl = apiUrls.file("document.pdf");
// Result: http://localhost:8000/api/documents/files/document.pdf

// Upload URLs with parameters
const uploadUrl = apiUrls.upload("fast");
// Result: http://localhost:8000/api/documents/upload?params_name=fast

// Query URLs
const queryUrl = apiUrls.query();
// Result: http://localhost:8000/api/query

// WebSocket URLs
const wsUrl = apiUrls.uploadProgressWebSocket();
// Result: ws://localhost:8000/ws/upload-progress
```

## Usage Examples

### 1. In Components

```typescript
import { apiUrls } from "../config/api";

// PDF Viewer
const pdfUrl = apiUrls.file(selectedResult.document_name);

// File Upload
const response = await axios.post(apiUrls.upload(paramSet), formData);

// Query Search
const response = await axios.post(apiUrls.query(), {
  query,
  params_name: paramSet,
});

// WebSocket Connection
const websocket = new WebSocket(apiUrls.uploadProgressWebSocket());
```

### 2. Environment Configuration

Create a `.env` file in the frontend directory:

```bash
# Development
VITE_API_BASE_URL=http://localhost:8000
VITE_WEBSOCKET_URL=ws://localhost:8000
VITE_API_DEBUG=true

# Production
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WEBSOCKET_URL=wss://api.yourdomain.com
VITE_API_DEBUG=false
VITE_API_TIMEOUT=60000
```

### 3. Custom Configuration

You can create custom configurations for different environments:

```typescript
import { ApiUrlBuilder } from "../config/api";

const customConfig = {
  baseUrl: "https://staging-api.yourdomain.com",
  websocketUrl: "wss://staging-api.yourdomain.com",
  timeout: 45000,
  debug: true,
};

const customBuilder = new ApiUrlBuilder(customConfig);
const customUrl = customBuilder.buildFileUrl("document.pdf");
```

## Migration Guide

### Before (Hardcoded URLs)

```typescript
// ❌ Hardcoded URLs
const pdfUrl = `http://localhost:8000/api/documents/files/${filename}`;
const uploadUrl = `http://localhost:8000/api/documents/upload?params_name=${paramSet}`;
const websocket = new WebSocket("ws://localhost:8000/ws/upload-progress");
```

### After (Configurable URLs)

```typescript
// ✅ Configurable URLs
import { apiUrls } from "../config/api";

const pdfUrl = apiUrls.file(filename);
const uploadUrl = apiUrls.upload(paramSet);
const websocket = new WebSocket(apiUrls.uploadProgressWebSocket());
```

## Production Deployment

### 1. Environment Variables

Set the following environment variables in your production environment:

```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WEBSOCKET_URL=wss://api.yourdomain.com
VITE_API_TIMEOUT=60000
VITE_API_DEBUG=false
```

### 2. Build Configuration

The configuration is baked into the build at compile time, so ensure environment variables are set before building:

```bash
# Set environment variables
export VITE_API_BASE_URL=https://api.yourdomain.com
export VITE_WEBSOCKET_URL=wss://api.yourdomain.com

# Build the application
npm run build
```

### 3. Docker Deployment

For Docker deployments, pass environment variables during build:

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
ARG VITE_API_BASE_URL
ARG VITE_WEBSOCKET_URL
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

```bash
docker build \
  --build-arg VITE_API_BASE_URL=https://api.yourdomain.com \
  --build-arg VITE_WEBSOCKET_URL=wss://api.yourdomain.com \
  -t your-app .
```

## Benefits

1. **Environment Flexibility**: Easy switching between development, staging, and production
2. **Maintainability**: All API endpoints defined in one place
3. **Type Safety**: TypeScript interfaces ensure correct configuration
4. **Debugging**: Built-in debug logging for development
5. **Security**: No hardcoded URLs in production builds
6. **Scalability**: Easy to add new endpoints and environments

## Testing

The configuration system includes test utilities:

```typescript
import { apiUrls } from "../config/api";

test("should construct correct URLs", () => {
  expect(apiUrls.file("test.pdf")).toBe(
    "http://localhost:8000/api/documents/files/test.pdf"
  );
  expect(apiUrls.query()).toBe("http://localhost:8000/api/query");
});
```

## Troubleshooting

### Common Issues

1. **Environment variables not loading**: Ensure variables start with `VITE_`
2. **WebSocket connection failing**: Check `VITE_WEBSOCKET_URL` configuration
3. **API timeouts**: Adjust `VITE_API_TIMEOUT` for slow networks
4. **Debug logs not showing**: Set `VITE_API_DEBUG=true` in development
5. **"process is not defined" error**: Use `import.meta.env` instead of `process.env` in Vite

### Vite Environment Variables

**Important**: Vite uses `import.meta.env` instead of `process.env`:

```typescript
// ❌ Wrong (Node.js style)
const apiUrl = process.env.VITE_API_BASE_URL;

// ✅ Correct (Vite style)
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

### Debug Mode

Enable debug mode to see configuration details:

```typescript
// Configuration will be logged to console in development
console.log("API Configuration:", {
  environment: import.meta.env.PROD ? "production" : "development",
  baseUrl: apiConfig.baseUrl,
  websocketUrl: apiConfig.websocketUrl,
  timeout: apiConfig.timeout,
});
```
