// src/frontend/src/config/services.ts
import { Storage, Dns, Api, Security, Hub, Wifi } from '@mui/icons-material';

export interface ServiceConfig {
  id: string;
  name: string;
  displayName: string;
  icon: string; // Changed from React.ReactElement to string
  healthCheckUrl: string;
  enabled: boolean;
}

// Icon mapping for dynamic icon rendering
export const iconMapping = {
  Storage,
  Dns,
  Api,
  Security,
  Hub,
  Wifi,
};

export const serviceConfigs: ServiceConfig[] = [
  {
    id: 'database',
    name: 'Supabase',
    displayName: 'Database: Supabase',
    icon: 'Storage',
    healthCheckUrl: '/api/health/database',
    enabled: true,
  },
  {
    id: 'llm',
    name: 'Ollama',
    displayName: 'LLM: Ollama',
    icon: 'Dns',
    healthCheckUrl: '/api/health/llm',
    enabled: true,
  },
  {
    id: 'api',
    name: 'FastAPI',
    displayName: 'API: FastAPI',
    icon: 'Api',
    healthCheckUrl: '/api/health',
    enabled: true,
  },
  {
    id: 'auth',
    name: 'Auth Service',
    displayName: 'Auth: Service',
    icon: 'Security',
    healthCheckUrl: '/api/health/auth',
    enabled: true,
  },
  {
    id: 'vector',
    name: 'ChromaDB',
    displayName: 'Vector: ChromaDB',
    icon: 'Hub',
    healthCheckUrl: '/api/health/vector',
    enabled: true,
  },
  {
    id: 'websocket',
    name: 'WebSocket',
    displayName: 'WebSocket',
    icon: 'Wifi',
    healthCheckUrl: '/api/health/websocket',
    enabled: true,
  },
];
