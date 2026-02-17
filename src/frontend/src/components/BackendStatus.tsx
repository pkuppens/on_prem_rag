import { useState, useEffect } from 'react';
import { Chip, Tooltip } from '@mui/material';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import { apiUrls } from '../config/api';

// BackendStatus component is responsible for checking and displaying backend health
export const BackendStatus = () => {
  // State for backend status and checking indicator
  const [isBackendRunning, setIsBackendRunning] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  // Function to check backend health
  const checkBackendStatus = async () => {
    try {
      setIsChecking(true);
      // Try to reach the health endpoint (static string)
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

  // Only check backend health once on mount
  useEffect(() => {
    checkBackendStatus();
    // No interval, only a single check
  }, []);

  // Render the status chip based on backend state
  if (isChecking) {
    return (
      <Tooltip title="Checking backend connection..." arrow>
        <Chip
          icon={<HourglassEmptyIcon />}
          label="Checking..."
          size="small"
          color="default"
          variant="outlined"
        />
      </Tooltip>
    );
  }

  if (isBackendRunning) {
    return (
      <Tooltip title="Backend is running" arrow>
        <Chip
          icon={<WifiIcon />}
          label="Backend Online"
          size="small"
          color="success"
          variant="outlined"
        />
      </Tooltip>
    );
  }

    return (
      <Tooltip title="Backend is offline. Check that the backend is running." arrow>
      <Chip
        icon={<WifiOffIcon />}
        label="Backend Offline"
        size="small"
        color="error"
        variant="outlined"
      />
    </Tooltip>
  );
};
