import { AppBar, Box, Button, Toolbar, Typography } from '@mui/material';
import { useAuth } from './AuthContext';
import { LoginForm } from './LoginForm';
import { useState } from 'react';

export const Header = () => {
  const { user, logout } = useAuth();
  const [showLogin, setShowLogin] = useState(false);

  return (
    <AppBar position="static" color="transparent" elevation={0}>
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          RAG Demo
        </Typography>
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
