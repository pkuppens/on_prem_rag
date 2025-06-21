import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Grid,
  Paper,
  TextField,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';
import { PDFViewer } from '../components/pdf/PDFViewer';
import { DOCXViewer } from '../components/docx/DOCXViewer';
import { TextViewer } from '../components/text/TextViewer';
import { pdfjs } from '../utils/pdfSetup';
import axios from 'axios';
import { RAGParamsSelector } from '../components/config/RAGParamsSelector';

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

export const QueryPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EmbeddingResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<EmbeddingResult | null>(null);
  const [paramSet, setParamSet] = useState('default');
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuery = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await axios.post('http://localhost:8000/api/query', {
        query,
        params_name: paramSet,
      });
      setResults(response.data.all_results || response.data);
      setSelectedResult(null);
    } catch (error) {
      console.error('Error querying:', error);
      setError('Failed to search documents. Please try again.');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResultSelect = (result: EmbeddingResult) => {
    setSelectedResult(result);
  };

  const getFileType = (filename: string) => {
    const extension = filename.split('.').pop()?.toLowerCase();
    return extension;
  };

  const renderViewer = () => {
    if (!selectedResult) return null;

    const fileType = getFileType(selectedResult.document_name);
    switch (fileType) {
      case 'pdf':
        return <PDFViewer selectedResult={selectedResult} />;
      case 'docx':
        return <DOCXViewer selectedResult={selectedResult} />;
      case 'txt':
      case 'md':
        return <TextViewer selectedResult={selectedResult} />;
      default:
        return (
          <Paper sx={{ p: 4, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              Preview not available for this file type
            </Typography>
          </Paper>
        );
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <TextField
                fullWidth
                label="Enter your query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
              />
              <Button variant="contained" onClick={handleQuery}>
                Search
              </Button>
            </Box>
            <Box sx={{ mt: 2 }}>
              <RAGParamsSelector value={paramSet} onChange={setParamSet} />
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>
              Search Results
            </Typography>

            {isLoading && (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            )}

            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {!isLoading && hasSearched && results.length === 0 && !error && (
              <Alert severity="info" sx={{ mb: 2 }}>
                No documents found matching your query. Try different keywords or check if documents have been uploaded.
              </Alert>
            )}

            {!isLoading && results.length > 0 && (
              <>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Found {results.length} result{results.length !== 1 ? 's' : ''}
                </Typography>
                {results.map((result, index) => (
                  <Paper
                    key={index}
                    sx={{
                      p: 2,
                      mb: 1,
                      cursor: 'pointer',
                      bgcolor: selectedResult === result ? 'action.selected' : 'background.paper',
                      '&:hover': {
                        bgcolor: 'action.hover',
                      },
                    }}
                    onClick={() => handleResultSelect(result)}
                  >
                    <Typography variant="subtitle2" noWrap>
                      {result.document_name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Score: {result.similarity_score.toFixed(3)}
                    </Typography>
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {result.text}
                    </Typography>
                  </Paper>
                ))}
              </>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          {renderViewer()}
        </Grid>
      </Grid>
    </Box>
  );
};
