import { useState } from 'react';
import { Box, Button, Paper, TextField, Typography, Slider, Tooltip, Alert, CircularProgress, InputAdornment } from '@mui/material';
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
  onResultSelect: (result: EmbeddingResult) => void;
}

export const QuerySection = ({ paramSet, onResultSelect }: Props) => {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState<string | null>(null);
  const [results, setResults] = useState<EmbeddingResult[]>([]);
  const [selected, setSelected] = useState(0);
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
      setResults(mapped);
      if (mapped.length > 0) {
        setSelected(0);
        onResultSelect(mapped[0]);
      }
    } catch (error) {
      console.error('Error querying:', error);
      const originalError = 'Failed to search documents. Please try again.';
      const enhancedError = enhanceErrorMessage(originalError, isBackendRunning, isChecking);
      setError(enhancedError);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResultSelect = (result: EmbeddingResult, index: number) => {
    setSelected(index);
    onResultSelect(result);
  };

  const handleSliderChange = (_event: Event, newValue: number | number[]) => {
    const value = Array.isArray(newValue) ? newValue[0] : newValue;
    setNumResults(value);
  };

  const handleSliderChangeCommitted = () => {
    // Re-run query when slider is released if we have existing results
    if (query.trim() && results.length > 0) {
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

      {!isLoading && hasSearched && results.length === 0 && !error && (
        <Alert severity="info" sx={{ mb: 2 }}>
          No relevant chunks found. Try different keywords or check if documents have been uploaded.
        </Alert>
      )}

      {!isLoading && results.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Sources ({results.length})
          </Typography>
          {results.map((r, idx) => (
            <Paper
              key={idx}
              onClick={() => handleResultSelect(r, idx)}
              sx={{
                p: 1.5,
                mb: 1,
                cursor: 'pointer',
                bgcolor: idx === selected ? 'action.selected' : undefined,
                '&:hover': {
                  bgcolor: idx === selected ? 'action.selected' : 'action.hover',
                },
              }}
            >
              <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>
                {r.document_name} • Page {
                  r.page_number === 'unknown' || r.page_number === undefined ? 'N/A' :
                  r.page_label && r.page_label !== 'unknown' && r.page_label !== String(r.page_number)
                    ? `${r.page_number} (${r.page_label})`
                    : r.page_number
                } • Chunk {r.chunk_index} • Score: {r.similarity_score.toFixed(3)}
              </Typography>
              <Tooltip
                title={r.text || 'No text content available'}
                placement="top"
                arrow
                enterDelay={500}
                leaveDelay={200}
              >
                <Typography variant="body2" sx={{ mt: 0.5, fontWeight: idx === selected ? 'medium' : 'normal' }}>
                  {r.text ? `${r.text.slice(0, 150)}${r.text.length > 150 ? '...' : ''}` : 'No text content available'}
                </Typography>
              </Tooltip>
            </Paper>
          ))}
        </Box>
      )}
    </Box>
  );
};
