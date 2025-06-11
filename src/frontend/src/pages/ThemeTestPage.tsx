import { useState } from 'react';
import { CssBaseline, ThemeProvider, createTheme, useMediaQuery, Box, Typography, Paper } from '@mui/material';
import { ThemeSelector, type ThemeMode } from '../components/theme/ThemeSelector';

function useAppTheme(mode: ThemeMode) {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
  return createTheme({
    palette: { mode: mode === 'system' ? (prefersDark ? 'dark' : 'light') : mode },
  });
}

export const ThemeTestPage = () => {
  const [mode, setMode] = useState<ThemeMode>('light');
  const theme = useAppTheme(mode);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ p: 4, minHeight: '100vh' }}>
        <Paper sx={{ p: 4, maxWidth: 600, mx: 'auto' }}>
          <Typography variant="h4" gutterBottom>
            Theme Selector Test Page
          </Typography>
          <Typography variant="body1" paragraph>
            This page tests the ThemeSelector component in isolation without authentication.
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Current theme mode: <strong>{mode}</strong>
          </Typography>
          <Box sx={{ mt: 3 }}>
            <ThemeSelector mode={mode} onChange={setMode} />
          </Box>
          <Typography variant="body2" sx={{ mt: 3 }}>
            Try switching between Light, Dark, and System themes to verify the component works correctly.
          </Typography>
        </Paper>
      </Box>
    </ThemeProvider>
  );
};
