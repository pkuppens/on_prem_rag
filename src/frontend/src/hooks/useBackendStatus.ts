import { useState, useEffect } from 'react';
import { apiUrlBuilder } from '../config/api';

export const useBackendStatus = () => {
  const [isBackendRunning, setIsBackendRunning] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  const checkBackendStatus = async () => {
    try {
      setIsChecking(true);
      // Use the URL builder to get the proper backend health endpoint
      const healthUrl = apiUrlBuilder.buildUrl('/health');
      const response = await fetch(healthUrl, {
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
