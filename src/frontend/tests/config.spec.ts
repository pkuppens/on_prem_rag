import { test, expect } from '@playwright/test';
import { apiUrls, apiConfig } from '../src/config/api';

test.describe('API Configuration', () => {
  test('should construct correct URLs in development', () => {
    // Test file URL construction
    expect(apiUrls.file('test.pdf')).toBe('http://localhost:8000/api/documents/files/test.pdf');

    // Test upload URL construction
    expect(apiUrls.upload('fast')).toBe('http://localhost:8000/api/documents/upload?params_name=fast');

    // Test query URL construction
    expect(apiUrls.query()).toBe('http://localhost:8000/api/query');

    // Test WebSocket URL construction
    expect(apiUrls.uploadProgressWebSocket()).toBe('ws://localhost:8000/ws/upload-progress');
  });

  test('should have correct configuration in development', () => {
    expect(apiConfig.baseUrl).toBe('http://localhost:8000');
    expect(apiConfig.websocketUrl).toBe('ws://localhost:8000');
    expect(apiConfig.timeout).toBe(30000);
    expect(apiConfig.debug).toBe(true);
  });

  test('should handle URL encoding correctly', () => {
    // Test with special characters in filename
    const filenameWithSpaces = 'my document.pdf';
    expect(apiUrls.file(filenameWithSpaces)).toBe('http://localhost:8000/api/documents/files/my%20document.pdf');

    // Test with special characters in parameter set
    const paramSetWithSpecialChars = 'fast&reliable';
    expect(apiUrls.upload(paramSetWithSpecialChars)).toBe('http://localhost:8000/api/documents/upload?params_name=fast%26reliable');
  });
});
