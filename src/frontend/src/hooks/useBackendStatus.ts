import { useState, useEffect } from 'react';
import { apiUrls } from '../config/api';

export const useBackendStatus = () => {
  const [isBackendRunning, setIsBackendRunning] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  const checkBackendStatus = async () => {
    try {
      setIsChecking(true);
      // Try to reach the health endpoint
      const response = await fetch(apiUrls.health(), {
        method: 'GET',
        signal: AbortSignal.timeout(3000), // 3 second timeout
      });
      setIsBackendRunning(response.ok);
    } catch (error) {
      setIsBackendRunning(false);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkBackendStatus();

    // Check every 30 seconds
    const interval = setInterval(checkBackendStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    isBackendRunning,
    isChecking,
    checkBackendStatus
  };
};
