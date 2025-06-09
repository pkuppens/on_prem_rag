import { CssBaseline, ThemeProvider, createTheme, useMediaQuery, Box, Grid, Container } from '@mui/material';
import { useMemo, useState, useEffect } from 'react';
import { ThemeTestPage } from './pages/ThemeTestPage';
import { AuthProvider } from './components/auth/AuthContext';
import { Header } from './components/auth/Header';
import { ThemeSelector, type ThemeMode } from './components/theme/ThemeSelector';
import { RAGParamsSelector } from './components/config/RAGParamsSelector';
import { FileDropzone } from './components/upload/FileDropzone';
import { UploadProgress } from './components/upload/UploadProgress';
import { QuerySection } from './components/query/QuerySection';
import { PDFViewer } from './components/pdf/PDFViewer';
import axios from 'axios';
import Logger from './utils/logger';
// Initialize PDF.js for secure on-premises deployment (must be imported early)
import './utils/pdfSetup';

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

interface UploadProgress {
  [key: string]: number;
}

interface EmbeddingResult {
  text: string;
  similarity_score: number;
  document_id: string;
  document_name: string;
  chunk_index: number;
  record_id: string;
  page_number: number | string;
}

function App() {
  const [mode, setMode] = useState<ThemeMode>('light');
  const [paramSet, setParamSet] = useState<string>('fast');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [selectedResult, setSelectedResult] = useState<EmbeddingResult | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const theme = useAppTheme(mode);

  // WebSocket setup for upload progress
  useEffect(() => {
    const websocket = new WebSocket('ws://localhost:8000/ws/upload-progress');

    websocket.onopen = () => {
      Logger.info('WebSocket connection established', 'App.tsx', 'useEffect', 47);
    };

    websocket.onmessage = (event) => {
      const progress = JSON.parse(event.data);
      Logger.debug('Received progress update', 'App.tsx', 'useEffect.onmessage', 51, progress);
      setUploadProgress(progress);
    };

    websocket.onerror = (error) => {
      Logger.error('WebSocket error occurred', 'App.tsx', 'useEffect.onerror', 56, error);
    };

    websocket.onclose = () => {
      Logger.info('WebSocket connection closed', 'App.tsx', 'useEffect.onclose', 60);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  // Check if we're on the test page
  const isTestPage = window.location.search.includes('test=theme');

  // If it's the test page, show only the test component without authentication
  if (isTestPage) {
    return <ThemeTestPage />;
  }

  const handleFileSelect = async (files: File[]) => {
    for (const file of files) {
      Logger.info(
        'Starting file upload',
        'App.tsx',
        'handleFileSelect',
        78,
        { filename: file.name, size: file.size, type: file.type, paramSet }
      );

      // Provide immediate feedback: set progress at 5% and yield to UI
      setUploadProgress(prev => ({ ...prev, [file.name]: 5 }));

      // Small async wait to give UI time to accept the progress update
      await new Promise(resolve => setTimeout(resolve, 100));

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post(
          `http://localhost:8000/api/documents/upload?params_name=${paramSet}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        Logger.info(
          'File upload completed',
          'App.tsx',
          'handleFileSelect',
          95,
          response.data
        );
      } catch (error) {
        Logger.error(
          'Error uploading file',
          'App.tsx',
          'handleFileSelect',
          102,
          error
        );
      }
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Header />
        <Container maxWidth="xl" sx={{ py: 2 }}>
          <Grid container spacing={3}>
            {/* Left Sidebar - 4 columns */}
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* 1. Theme Selector */}
                <ThemeSelector mode={mode} onChange={setMode} />

                {/* 2. Parameter Selector */}
                <RAGParamsSelector value={paramSet} onChange={setParamSet} />

                {/* 3. Drag/Drop Upload */}
                <Box>
                  <FileDropzone onFileSelect={handleFileSelect} />
                  {Object.entries(uploadProgress).map(([filename, progress]) => (
                    <UploadProgress
                      key={filename}
                      filename={filename}
                      progress={progress}
                    />
                  ))}
                </Box>

                {/* 4. Keyword Query with Search */}
                <QuerySection
                  paramSet={paramSet}
                  onResultSelect={setSelectedResult}
                />
              </Box>
            </Grid>

            {/* Right Area - 8 columns */}
            <Grid item xs={12} md={8}>
              <PDFViewer selectedResult={selectedResult} />
            </Grid>
          </Grid>
        </Container>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
