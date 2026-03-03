import { useState } from 'react';
import { Box, Button, Chip, Paper, TextField, Typography, Slider, Alert, CircularProgress, InputAdornment } from '@mui/material';
import axios from 'axios';
import { apiUrls } from '../../config/api';
import { useBackendStatus } from '../../hooks/useBackendStatus';
import { enhanceErrorMessage } from '../../utils/errorUtils';
import { VoiceInputButton } from './VoiceInputButton';

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

interface AskResponse {
  answer: string;
  sources: Array<{
    document_name: string;
    page_number: number | string;
    similarity_score: number;
    text_preview: string;
  }>;
  confidence: string;
  chunks_retrieved: number;
  average_similarity: number;
}

interface Props {
  paramSet: string;
  sources: EmbeddingResult[];
  selectedSourceIndex: number;
  onResultsChange: (results: EmbeddingResult[]) => void;
  onSourceSelect: (index: number, result: EmbeddingResult) => void;
}

export const QuerySection = ({ paramSet, sources, selectedSourceIndex, onResultsChange, onSourceSelect }: Props) => {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [numResults, setNumResults] = useState(5); // Default to 5 results
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isBackendRunning, isChecking } = useBackendStatus();

  const runQuery = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    setAnswer(null);

    try {
      const res = await axios.post<AskResponse>(apiUrls.ask(), {
        question: query,
        strategy: 'hybrid',
        top_k: numResults,
      });
      setAnswer(res.data.answer);
      const mapped: EmbeddingResult[] = res.data.sources.map((s, idx) => ({
        text: s.text_preview,
        similarity_score: s.similarity_score,
        document_id: s.document_name,
        document_name: s.document_name,
        chunk_index: idx,
        record_id: '',
        page_number: s.page_number,
      }));
      onResultsChange(mapped);
      if (mapped.length > 0) {
        onSourceSelect(0, mapped[0]);
      }
    } catch (error) {
      console.error('Error querying:', error);
      const originalError = 'Failed to search documents. Please try again.';
      const enhancedError = enhanceErrorMessage(originalError, isBackendRunning, isChecking);
      setError(enhancedError);
      onResultsChange([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCitationClick = (index: number, result: EmbeddingResult) => {
    onSourceSelect(index, result);
    document.getElementById(`source-${index}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  };

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    const value = Array.isArray(newValue) ? newValue[0] : newValue;
    setNumResults(value);
  };

  const handleSliderChangeCommitted = () => {
    if (query.trim() && sources.length > 0) {
      runQuery();
    }
  };

  return (
    <Box>
      <TextField
        fullWidth
        label="Ask a question"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        sx={{ mb: 2 }}
        size="medium"
        variant="outlined"
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            runQuery();
          }
        }}
        InputProps={{
          endAdornment: (
            <InputAdornment position="end">
              <VoiceInputButton
                onTranscription={(text) => setQuery(text)}
                onError={(msg) => setError(msg)}
                disabled={!isBackendRunning || isChecking}
              />
            </InputAdornment>
          ),
        }}
      />

      {/* Number of Results Slider */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="body2" sx={{ mb: 1 }}>
          Number of Results: {numResults}
        </Typography>
        <Slider
          value={numResults}
          onChange={handleSliderChange}
          onChangeCommitted={handleSliderChangeCommitted}
          aria-labelledby="results-slider"
          valueLabelDisplay="auto"
          step={1}
          marks
          min={1}
          max={10}
          sx={{ mb: 1 }}
        />
      </Box>

      <Button
        variant="contained"
        fullWidth
        onClick={runQuery}
        sx={{ mb: 2 }}
        disabled={!query.trim() || isLoading}
      >
        {isLoading ? 'Answering...' : 'Ask'}
      </Button>

      {answer && (
        <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
          <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
            Answer
          </Typography>
          <Typography variant="body1">{answer}</Typography>
          {sources.length > 0 && (
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1.5 }}>
              {sources.map((_r, idx) => (
                <Chip
                  key={idx}
                  label={idx + 1}
                  size="small"
                  variant={idx === selectedSourceIndex ? 'filled' : 'outlined'}
                  onClick={() => handleCitationClick(idx, sources[idx])}
                  sx={{ cursor: 'pointer' }}
                  aria-label={`View source ${idx + 1}`}
                />
              ))}
            </Box>
          )}
        </Paper>
      )}

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
          <CircularProgress size={24} />
        </Box>
      )}

      {error && (
        <Alert
          severity="error"
          sx={{
            mb: 2,
            '& .MuiAlert-message': {
              whiteSpace: 'pre-line' // Preserve line breaks for enhanced error messages
            }
          }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                setError(null);
                if (query.trim()) {
                  runQuery();
                }
              }}
            >
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      {!isLoading && hasSearched && sources.length === 0 && !error && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No relevant chunks found. Try different keywords or check if documents have been uploaded.
        </Alert>
      )}

    </Box>
  );
};
