import { AppBar, Box, Button, Toolbar, Typography, Chip, Tooltip } from '@mui/material';
import { useAuth } from './AuthContext';
import { LoginForm } from './LoginForm';
import { useState } from 'react';
import { useBackendStatus } from '../../hooks/useBackendStatus';
import WifiIcon from '@mui/icons-material/Wifi';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';

export const Header = () => {
  const { user, logout } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const { isBackendRunning, isChecking } = useBackendStatus();

  const getBackendStatusChip = () => {
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
      <Tooltip title="Backend is offline. Please start the backend server at http://localhost:8000" arrow>
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

  return (
    <AppBar position="static" color="transparent" elevation={0}>
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          RAG Demo
        </Typography>

        {/* Backend Status Indicator */}
        <Box sx={{ mr: 2 }}>
          {getBackendStatusChip()}
        </Box>

        {user ? (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography>{user.username}</Typography>
            <Button color="inherit" onClick={logout}>
              Logout
            </Button>
          </Box>
        ) : showLogin ? (
          <LoginForm />
        ) : (
          <Button color="inherit" onClick={() => setShowLogin(true)}>
            Login
          </Button>
        )}
      </Toolbar>
    </AppBar>
  );
};
