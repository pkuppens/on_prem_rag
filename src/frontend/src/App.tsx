import { CssBaseline, ThemeProvider, createTheme, useMediaQuery, Box, Grid, Container } from '@mui/material';
import { useMemo, useState } from 'react';
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
import { useBackendStatus } from './hooks/useBackendStatus';
import { enhanceErrorMessage } from './utils/errorUtils';
// Initialize PDF.js for secure on-premises deployment (must be imported early)
import './utils/pdfSetup';
import { PDFTestPage } from './pages/PDFTestPage';
import DocxTestPage from './pages/DocxTestPage';
import TextTestPage from './pages/TextTestPage';
import { WebSocketTestPage } from './pages/WebSocketTestPage';
import StatusPage from './pages/StatusPage'; // Import the new StatusPage
import { apiUrls, apiConfig } from './config/api';
import { useWebSocket } from './hooks/useWebSocket';

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
  [key: string]: {
    progress: number;
    error?: string;
    isComplete?: boolean;
  };
}

interface EmbeddingResult {
  text: string;
  similarity_score: number;
  document_id: string;
  document_name: string;
  chunk_index: number;
  record_id: string;
  page_number: number | string;
  page_label?: string;
}

function App() {
  const [mode, setMode] = useState<ThemeMode>('light');
  const [paramSet, setParamSet] = useState<string>('fast');
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [selectedResult, setSelectedResult] = useState<EmbeddingResult | null>(null);
  const theme = useAppTheme(mode);
  const { isBackendRunning, isChecking } = useBackendStatus();

  // WebSocket setup for upload progress using the custom hook
  const { isConnected: wsConnected } = useWebSocket({
    url: apiUrls.uploadProgressWebSocket(),
    onMessage: (data) => {
      Logger.debug('Received progress update', 'App.tsx', 'useWebSocket.onMessage', 47, data);
      setUploadProgress(prev => ({
        ...prev,
        [data.file_id]: {
          progress: data.progress,
          error: data.error,
          isComplete: data.isComplete
        }
      }));
    },
    onError: (error) => {
      Logger.error('WebSocket error occurred', 'App.tsx', 'useWebSocket.onError', 56, error);
    },
    onOpen: () => {
      Logger.info('WebSocket connection established', 'App.tsx', 'useWebSocket.onOpen', 60);
    },
    onClose: () => {
      Logger.info('WebSocket connection closed', 'App.tsx', 'useWebSocket.onClose', 63);
    },
    reconnectInterval: 5000,
    maxReconnectAttempts: 5,
    pingInterval: 30000,
  });

  // Check if we're on test pages
  const isThemeTestPage = window.location.search.includes('test=theme');
  const isPDFTestPage = window.location.search.includes('test=pdf');
  const isDocxTestPage = window.location.search.includes('test=docx');
  const isTextTestPage = window.location.search.includes('test=text');
  const isWebSocketTestPage = window.location.search.includes('test=websocket');
  const isStatusPage = window.location.search.includes('test=status');

  // If it's a test page, show only the test component without authentication
  if (isThemeTestPage) {
    return <ThemeTestPage />;
  }
  if (isStatusPage) {
    return <StatusPage />;
  }

  if (isPDFTestPage) {
    return <PDFTestPage />;
  }
  if (isDocxTestPage) {
    return <DocxTestPage />;
  }
  if (isTextTestPage) {
    return <TextTestPage />;
  }

  if (isWebSocketTestPage) {
    return <WebSocketTestPage />;
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
      setUploadProgress(prev => ({
        ...prev,
        [file.name]: {
          progress: 5,
          isComplete: false
        }
      }));

      // Small async wait to give UI time to accept the progress update
      await new Promise(resolve => setTimeout(resolve, 100));

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post(
          apiUrls.upload(paramSet),
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

        // Mark upload as complete
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: {
            ...prev[file.name],
            progress: 100,
            isComplete: true
          }
        }));
      } catch (error) {
        Logger.error(
          'Error uploading file',
          'App.tsx',
          'handleFileSelect',
          102,
          error
        );

        // Set error state with enhanced message
        const originalError = error instanceof Error ? error.message : 'Upload failed';
        const enhancedError = enhanceErrorMessage(originalError, isBackendRunning, isChecking);
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: {
            ...prev[file.name],
            error: enhancedError
          }
        }));
      }
    }
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Header />
        <Box sx={{ py: 2, px: 3, width: '100%' }}>
          <Grid container spacing={3}>
            {/* Left Sidebar - 3 columns for ultrawide */}
            <Grid item xs={12} lg={3} xl={2}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {/* 1. Theme Selector */}
                <ThemeSelector mode={mode} onChange={setMode} />

                {/* 2. Parameter Selector */}
                <RAGParamsSelector value={paramSet} onChange={setParamSet} />

                {/* 3. Drag/Drop Upload */}
                <Box>
                  <FileDropzone onFileSelect={handleFileSelect} />
                  {Object.entries(uploadProgress).map(([filename, data]) => (
                    <UploadProgress
                      key={filename}
                      filename={filename}
                      progress={data.progress}
                      error={data.error}
                      isComplete={data.isComplete}
                      onComplete={() => {
                        // Remove the completed upload from the progress list
                        setUploadProgress(prev => {
                          const newProgress = { ...prev };
                          delete newProgress[filename];
                          return newProgress;
                        });
                      }}
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

            {/* Right Area - 9 columns for ultrawide */}
            <Grid item xs={12} lg={9} xl={10}>
              <PDFViewer selectedResult={selectedResult} />
            </Grid>
          </Grid>
        </Box>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
