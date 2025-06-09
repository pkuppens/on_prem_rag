import { CssBaseline, ThemeProvider, createTheme, useMediaQuery, Box } from '@mui/material';
import { useMemo, useState } from 'react';
import { UploadPage } from './pages/UploadPage';
import { QueryPage } from './pages/QueryPage';
import { AuthProvider } from './components/auth/AuthContext';
import { Header } from './components/auth/Header';
import { ThemeSelector, ThemeMode } from './components/theme/ThemeSelector';

function useAppTheme(mode: ThemeMode) {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
  return useMemo(
    () =>
      createTheme({
        palette: { mode: mode === 'system' ? (prefersDark ? 'dark' : 'light') : mode },
      }),
    [mode, prefersDark],
  );
}

function App() {
  const [mode, setMode] = useState<ThemeMode>('light');
  const theme = useAppTheme(mode);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Header />
        <Box sx={{ p: 2 }}>
          <ThemeSelector mode={mode} onChange={setMode} />
        </Box>
        <UploadPage />
        <QueryPage />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
