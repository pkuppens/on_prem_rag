import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Grid,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import { PDFViewer } from '../components/pdf/PDFViewer';
import { DOCXViewer } from '../components/docx/DOCXViewer';
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

  const handleQuery = async () => {
    try {
      const response = await axios.post('http://localhost:8000/api/query', {
        query,
        params_name: paramSet,
      });
      setResults(response.data);
      setSelectedResult(null);
    } catch (error) {
      console.error('Error querying:', error);
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
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          {renderViewer()}
        </Grid>
      </Grid>
    </Box>
  );
};
