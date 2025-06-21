import { useState, useEffect } from 'react';
import { Document, Page } from 'react-pdf';
import { pdfjs } from '../utils/pdfSetup';
import {
  Container,
  Typography,
  Paper,
  Box,
  Button,
  Alert,
  CircularProgress,
  Link
} from '@mui/material';
import { FileDropzone } from '../components/upload/FileDropzone';
import { UploadProgress } from '../components/upload/UploadProgress';
import axios from 'axios';
import Logger from '../utils/logger';

// Test URL for the uploaded PDF
const TEST_PDF_URL = 'http://localhost:8000/files/2303.18223v16.pdf';

export const PDFTestPage = () => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<{
    [key: string]: {
      progress: number;
      error?: string;
      isComplete?: boolean;
    }
  }>({});
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [currentPdfUrl, setCurrentPdfUrl] = useState<string>(TEST_PDF_URL);

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8000/ws/upload-progress');

    websocket.onopen = () => {
      Logger.info('WebSocket connection established', 'PDFTestPage.tsx', 'useEffect', 20);
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      Logger.debug('Received progress update', 'PDFTestPage.tsx', 'useEffect.onmessage', 27, data);
      setUploadProgress(prev => ({
        ...prev,
        [data.file_id]: {
          progress: data.progress,
          error: data.error,
          isComplete: data.isComplete
        }
      }));
    };

    websocket.onerror = (error) => {
      Logger.error('WebSocket error occurred', 'PDFTestPage.tsx', 'useEffect.onerror', 35, error);
      setError('Failed to connect to upload progress server. Please check if the backend is running.');
    };

    websocket.onclose = () => {
      Logger.info('WebSocket connection closed', 'PDFTestPage.tsx', 'useEffect.onclose', 42);
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  const handleFileSelect = async (files: File[]) => {
    for (const file of files) {
      Logger.info('Starting file upload', 'PDFTestPage.tsx', 'handleFileSelect', 55, {
        filename: file.name,
        size: file.size,
        type: file.type
      });

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post(
          'http://localhost:8000/api/documents/upload',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        Logger.info('File upload completed', 'PDFTestPage.tsx', 'handleFileSelect', 70, response.data);

        // Mark upload as complete
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: {
            ...prev[file.name],
            progress: 100,
            isComplete: true
          }
        }));

        // Update the PDF URL to show the newly uploaded file
        if (file.name.toLowerCase().endsWith('.pdf')) {
          setCurrentPdfUrl(`http://localhost:8000/files/${file.name}`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
        Logger.error('Error uploading file', 'PDFTestPage.tsx', 'handleFileSelect', 77, error);
        setError(`Failed to upload file: ${errorMessage}`);

        // Set error state in progress
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: {
            ...prev[file.name],
            error: errorMessage
          }
        }));
      }
    }
  };

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
    console.log('PDF loaded successfully:', { numPages, pdfVersion: pdfjs.version });
  };

  const onDocumentLoadError = (error: Error) => {
    setLoading(false);
    setError(`Failed to load PDF: ${error.message}`);
    console.error('PDF load error:', error);
  };

  const onLoadStart = () => {
    setLoading(true);
    setError(null);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        PDF Test Page
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Configuration Status:
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          <strong>React-PDF Version:</strong> {pdfjs.version}
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          <strong>Worker Source:</strong> {pdfjs.GlobalWorkerOptions.workerSrc}
        </Typography>
        <Typography variant="body2">
          <strong>Test PDF:</strong> <Link href={currentPdfUrl} target="_blank" rel="noopener noreferrer">{currentPdfUrl}</Link>
        </Typography>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Upload PDF
        </Typography>
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
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>Error:</strong> {error}
          </Typography>
        </Alert>
      )}

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
          <CircularProgress />
          <Typography variant="body2" sx={{ ml: 2, alignSelf: 'center' }}>
            Loading PDF...
          </Typography>
        </Box>
      )}

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            PDF Viewer Test
          </Typography>
          {numPages > 0 && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button
                onClick={() => setPageNumber(page => Math.max(1, page - 1))}
                disabled={pageNumber <= 1}
                size="small"
                variant="outlined"
              >
                Previous
              </Button>
              <Typography variant="body2" sx={{ minWidth: '100px', textAlign: 'center' }}>
                Page {pageNumber} of {numPages}
              </Typography>
              <Button
                onClick={() => setPageNumber(page => Math.min(numPages, page + 1))}
                disabled={pageNumber >= numPages}
                size="small"
                variant="outlined"
              >
                Next
              </Button>
            </Box>
          )}
        </Box>

        <Box sx={{
          display: 'flex',
          justifyContent: 'center',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          minHeight: '400px',
          alignItems: 'center'
        }}>
          <Document
            file={currentPdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            onLoadStart={onLoadStart}
            loading={
              <Box sx={{ textAlign: 'center' }}>
                <CircularProgress size={40} />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Loading PDF document...
                </Typography>
              </Box>
            }
            error={
              <Alert severity="error">
                <Typography>
                  Failed to load PDF document. Check console for details.
                </Typography>
              </Alert>
            }
          >
            {numPages > 0 && (
              <Page
                pageNumber={pageNumber}
                width={Math.min(800, window.innerWidth * 0.8)}
                renderTextLayer={false}
                renderAnnotationLayer={false}
                loading={
                  <Box sx={{ textAlign: 'center', p: 4 }}>
                    <CircularProgress size={30} />
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Rendering page...
                    </Typography>
                  </Box>
                }
                error={
                  <Alert severity="error">
                    Failed to render page {pageNumber}
                  </Alert>
                }
              />
            )}
          </Document>
        </Box>
      </Paper>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Debug Information:
        </Typography>
        <Typography variant="body2" component="pre" sx={{
          fontFamily: 'monospace',
          fontSize: '0.75rem',
          whiteSpace: 'pre-wrap',
          backgroundColor: 'grey.100',
          p: 1,
          borderRadius: 1
        }}>
          {JSON.stringify({
            workerSrc: pdfjs.GlobalWorkerOptions.workerSrc,
            version: pdfjs.version,
            testUrl: currentPdfUrl,
            currentPage: pageNumber,
            totalPages: numPages,
            loading,
            error: error || 'none'
          }, null, 2)}
        </Typography>
      </Paper>
    </Container>
  );
};
