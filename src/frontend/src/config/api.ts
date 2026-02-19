/**
 * API Configuration and Utilities
 *
 * This module provides centralized configuration for API endpoints,
 * environment-specific settings, and utility functions for constructing URLs.
 */

// Environment detection
const isDevelopment = import.meta.env.DEV;
const isProduction = import.meta.env.PROD;

// API Configuration
export interface ApiConfig {
  /** Base URL for the backend API */
  baseUrl: string;
  /** WebSocket URL for real-time updates */
  websocketUrl: string;
  /** Timeout for API requests in milliseconds */
  timeout: number;
  /** Whether to enable debug logging */
  debug: boolean;
}

// Default configuration for development
// VITE_BACKEND_URL is set by docker-compose (e.g. http://localhost:9180)
const defaultConfig: ApiConfig = {
  baseUrl: 'http://localhost:8000',
  websocketUrl: 'ws://localhost:8000',
  timeout: 30000,
  debug: true,
};

// Production configuration
const productionConfig: ApiConfig = {
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'https://api.yourdomain.com',
  websocketUrl: import.meta.env.VITE_WEBSOCKET_URL || 'wss://api.yourdomain.com',
  timeout: 60000,
  debug: false,
};

// Get configuration based on environment
export const getApiConfig = (): ApiConfig => {
  if (isProduction) {
    return productionConfig;
  }

  // Development environment - allow override via environment variables
  // VITE_BACKEND_URL is set by docker-compose; VITE_API_BASE_URL takes precedence
  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_BACKEND_URL ||
    defaultConfig.baseUrl;
  const wsBase = baseUrl.replace(/^http/, 'ws');
  return {
    baseUrl,
    websocketUrl: import.meta.env.VITE_WEBSOCKET_URL || wsBase,
    timeout: parseInt(import.meta.env.VITE_API_TIMEOUT || defaultConfig.timeout.toString()),
    debug: import.meta.env.VITE_API_DEBUG !== 'false', // Default to true in dev
  };
};

// API Endpoints
export const API_ENDPOINTS = {
  // Document management
  DOCUMENTS: {
    UPLOAD: '/api/documents/upload',
    LIST: '/api/documents/list',
    FILES: '/api/documents/files',
  },
  // Query and search
  QUERY: {
    SEARCH: '/api/query',
  },
  // Question answering (hybrid retrieval)
  ASK: '/api/ask',
  ASK_VOICE: '/api/ask/voice',
  // Speech-to-text
  STT: {
    TRANSCRIBE: '/api/stt/transcribe',
    TRANSCRIBE_DRAFT: '/api/stt/transcribe/draft',
    INFO: '/api/stt/info',
  },
  // Parameters
  PARAMETERS: {
    LIST: '/api/parameters',
  },
  // Health check
  HEALTH: {
    STATUS: '/api/health',
  },
  // WebSocket
  WEBSOCKET: {
    UPLOAD_PROGRESS: '/ws/upload-progress',
  },
} as const;

// Utility functions for constructing URLs
export class ApiUrlBuilder {
  private config: ApiConfig;

  constructor(config?: Partial<ApiConfig>) {
    this.config = { ...getApiConfig(), ...config };
  }

  /**
   * Build a complete API URL
   * @param endpoint - The API endpoint path
   * @returns Complete URL with base URL
   */
  buildUrl(endpoint: string): string {
    const baseUrl = this.config.baseUrl.replace(/\/$/, ''); // Remove trailing slash
    const cleanEndpoint = endpoint.replace(/^\//, ''); // Remove leading slash
    return `${baseUrl}/${cleanEndpoint}`;
  }

  /**
   * Build a file serving URL
   * @param filename - The filename to serve
   * @returns Complete file URL
   */
  buildFileUrl(filename: string): string {
    return this.buildUrl(`${API_ENDPOINTS.DOCUMENTS.FILES}/${encodeURIComponent(filename)}`);
  }

  /**
   * Build a WebSocket URL
   * @param endpoint - The WebSocket endpoint path
   * @returns Complete WebSocket URL
   */
  buildWebSocketUrl(endpoint: string): string {
    const baseUrl = this.config.websocketUrl.replace(/\/$/, '');
    const cleanEndpoint = endpoint.replace(/^\//, '');
    return `${baseUrl}/${cleanEndpoint}`;
  }

  /**
   * Get the upload progress WebSocket URL
   * @returns WebSocket URL for upload progress
   */
  getUploadProgressWebSocketUrl(): string {
    return this.buildWebSocketUrl(API_ENDPOINTS.WEBSOCKET.UPLOAD_PROGRESS);
  }

  /**
   * Get the document upload URL
   * @param paramsName - Optional parameter set name
   * @returns Upload URL with optional query parameters
   */
  getUploadUrl(paramsName?: string): string {
    let url = this.buildUrl(API_ENDPOINTS.DOCUMENTS.UPLOAD);
    if (paramsName) {
      url += `?params_name=${encodeURIComponent(paramsName)}`;
    }
    return url;
  }

  /**
   * Get the query search URL
   * @returns Query search URL
   */
  getQueryUrl(): string {
    return this.buildUrl(API_ENDPOINTS.QUERY.SEARCH);
  }

  /**
   * Get the ask (QA with hybrid retrieval) URL
   * @returns Ask endpoint URL
   */
  getAskUrl(): string {
    return this.buildUrl(API_ENDPOINTS.ASK);
  }

  getAskVoiceUrl(): string {
    return this.buildUrl(API_ENDPOINTS.ASK_VOICE);
  }

  getSttTranscribeDraftUrl(): string {
    return this.buildUrl(API_ENDPOINTS.STT.TRANSCRIBE_DRAFT);
  }

  getSttInfoUrl(): string {
    return this.buildUrl(API_ENDPOINTS.STT.INFO);
  }

  /**
   * Get the parameters list URL
   * @returns Parameters list URL
   */
  getParametersUrl(): string {
    return this.buildUrl(API_ENDPOINTS.PARAMETERS.LIST);
  }

  /**
   * Get the parameter sets URL
   * @returns Parameter sets URL
   */
  getParameterSetsUrl(): string {
    return this.buildUrl(`${API_ENDPOINTS.PARAMETERS.LIST}/sets`);
  }

  /**
   * Get the health check URL
   * @returns Health check URL
   */
  getHealthUrl(): string {
    return this.buildUrl(API_ENDPOINTS.HEALTH.STATUS);
  }
}

// Default API URL builder instance
export const apiUrlBuilder = new ApiUrlBuilder();

// Convenience functions for common operations
export const apiUrls = {
  /**
   * Get file URL for a specific filename
   */
  file: (filename: string) => apiUrlBuilder.buildFileUrl(filename),

  /**
   * Get upload URL with optional parameter set
   */
  upload: (paramsName?: string) => apiUrlBuilder.getUploadUrl(paramsName),

  /**
   * Get query search URL
   */
  query: () => apiUrlBuilder.getQueryUrl(),

  /**
   * Get ask (QA with hybrid retrieval) URL
   */
  ask: () => apiUrlBuilder.getAskUrl(),

  askVoice: () => apiUrlBuilder.getAskVoiceUrl(),

  sttTranscribeDraft: () => apiUrlBuilder.getSttTranscribeDraftUrl(),

  sttInfo: () => apiUrlBuilder.getSttInfoUrl(),

  /**
   * Get parameters list URL
   */
  parameters: () => apiUrlBuilder.getParametersUrl(),

  /**
   * Get parameter sets URL
   */
  parameterSets: () => apiUrlBuilder.getParameterSetsUrl(),

  /**
   * Get health check URL (full URL including backend base)
   */
  health: () => apiUrlBuilder.buildUrl('/health'),

  /**
   * Get upload progress WebSocket URL
   */
  uploadProgressWebSocket: () => apiUrlBuilder.getUploadProgressWebSocketUrl(),
};

// Export configuration for use in other modules
export const apiConfig = getApiConfig();

// Debug logging in development
if (apiConfig.debug) {
  console.log('API Configuration:', {
    environment: isProduction ? 'production' : 'development',
    baseUrl: apiConfig.baseUrl,
    websocketUrl: apiConfig.websocketUrl,
    timeout: apiConfig.timeout,
  });
}
