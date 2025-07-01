/**
 * Error message enhancement utilities
 * Provides helpful hints when backend connectivity issues are detected
 */

export const enhanceErrorMessage = (
  originalError: string,
  isBackendRunning: boolean | null,
  isChecking: boolean = false
): string => {
  // If we're still checking backend status, return original error
  if (isChecking) {
    return originalError;
  }

  // If backend is confirmed to be running, return original error
  if (isBackendRunning === true) {
    return originalError;
  }

  // If backend is not running, enhance the error message
  if (isBackendRunning === false) {
    const backendHint = '\n\n💡 Hint: The backend server appears to be offline. Please check if the backend is running at http://localhost:8000';
    return `${originalError}${backendHint}`;
  }

  // If backend status is unknown, add a general hint
  return `${originalError}\n\n💡 Hint: Unable to connect to the backend. Please ensure the backend server is running.`;
};

/**
 * Check if an error is likely a network/connectivity issue
 */
export const isNetworkError = (error: any): boolean => {
  if (!error) return false;

  // Check for common network error patterns
  const errorMessage = error.message?.toLowerCase() || '';
  const errorString = String(error).toLowerCase();

  return (
    errorMessage.includes('network') ||
    errorMessage.includes('fetch') ||
    errorMessage.includes('connection') ||
    errorMessage.includes('timeout') ||
    errorString.includes('network') ||
    errorString.includes('fetch') ||
    errorString.includes('connection') ||
    errorString.includes('timeout') ||
    error.code === 'NETWORK_ERROR' ||
    error.code === 'ERR_NETWORK' ||
    error.name === 'TypeError' && errorMessage.includes('fetch')
  );
};
