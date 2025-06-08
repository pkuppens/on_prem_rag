import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { UploadPage } from './pages/UploadPage';
import { AuthProvider } from './components/auth/AuthContext';
import { Header } from './components/auth/Header';

const theme = createTheme({
  palette: {
    mode: 'light',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Header />
        <UploadPage />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
