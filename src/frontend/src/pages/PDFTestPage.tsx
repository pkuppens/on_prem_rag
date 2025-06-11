import { useState } from 'react';
import { Document, Page } from 'react-pdf';
import { pdfjs } from '../utils/pdfSetup';
import {
  Container,
  Typography,
  Paper,
  Box,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';

// Test URL for the uploaded PDF
const TEST_PDF_URL = 'http://localhost:8000/files/2303.18223v16.pdf';

export const PDFTestPage = () => {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

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
          <strong>Test PDF:</strong> {TEST_PDF_URL}
        </Typography>
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

      <Paper sx={{ p: 2 }}>
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
            file={TEST_PDF_URL}
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

      <Paper sx={{ p: 2, mt: 3 }}>
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
            testUrl: TEST_PDF_URL,
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
