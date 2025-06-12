import { useState, useEffect } from 'react';
import { Box, Button, Typography, Paper } from '@mui/material';
import { Document as PDFDocument, Page } from 'react-pdf';
import { pdfjs } from '../../utils/pdfSetup';
import Logger from '../../utils/logger';

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

interface Props {
  selectedResult: EmbeddingResult | null;
}

export const PDFViewer = ({ selectedResult }: Props) => {
  const [page, setPage] = useState(1);
  const [numPages, setNumPages] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedResult) {
      const pageNum = Number(selectedResult.page_number);
      setPage(pageNum && pageNum > 0 ? pageNum : 1);
      setError(null);

      // Log the PDF URL for debugging
      const pdfUrl = `http://localhost:8000/files/${selectedResult.document_name}`;
      Logger.info('Loading PDF', 'PDFViewer.tsx', 'useEffect', 29, {
        pdfUrl,
        document_name: selectedResult.document_name,
        page_number: selectedResult.page_number
      });
    }
  }, [selectedResult]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setError(null);
    Logger.info('PDF loaded successfully', 'PDFViewer.tsx', 'onDocumentLoadSuccess', 40, { numPages });
  };

  const onDocumentLoadError = (error: Error) => {
    const errorMessage = `Failed to load PDF: ${error.message}`;
    setError(errorMessage);
    Logger.error('PDF load error', 'PDFViewer.tsx', 'onDocumentLoadError', 45, {
      error: error.message,
      document_name: selectedResult?.document_name
    });
  };

  if (!selectedResult) {
    return (
      <Paper sx={{ p: 4, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Select a search result to view the PDF document
        </Typography>
      </Paper>
    );
  }

  const pdfUrl = `http://localhost:8000/files/${selectedResult.document_name}`;

  return (
    <Paper sx={{ p: 2, height: 'fit-content' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" noWrap>
          {selectedResult.document_name}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            size="small"
          >
            Previous
          </Button>
          <Typography variant="body2" sx={{ minWidth: '80px', textAlign: 'center' }}>
            Page {page} of {numPages}
          </Typography>
          <Button
            onClick={() => setPage((p) => Math.min(numPages, p + 1))}
            disabled={page >= numPages}
            size="small"
          >
            Next
          </Button>
        </Box>
      </Box>

      {error && (
        <Box sx={{ mb: 2 }}>
          <Typography color="error" variant="body2">
            {error}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Trying to load: {pdfUrl}
          </Typography>
        </Box>
      )}

      <Box sx={{
        display: 'flex',
        justifyContent: 'center',
        border: '1px solid',
        borderColor: 'divider',
        borderRadius: 1,
        overflow: 'auto',
        maxHeight: '80vh'
      }}>
        <PDFDocument
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          error={
            <Typography color="error" sx={{ p: 2 }}>
              Failed to load PDF. Please check if the file exists at: {pdfUrl}
            </Typography>
          }
          loading={
            <Typography sx={{ p: 2 }}>
              Loading PDF...
            </Typography>
          }
        >
          <Page
            pageNumber={page}
            width={Math.min(800, window.innerWidth * 0.6)}
            renderTextLayer={false}
            renderAnnotationLayer={false}
          />
        </PDFDocument>
      </Box>
    </Paper>
  );
};
