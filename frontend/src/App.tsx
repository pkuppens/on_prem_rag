import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { UploadPage } from './pages/UploadPage';

const theme = createTheme({
  palette: {
    mode: 'light',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <UploadPage />
    </ThemeProvider>
  );
}

export default App;
