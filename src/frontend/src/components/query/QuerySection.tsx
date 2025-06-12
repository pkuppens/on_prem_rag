import { useState } from 'react';
import { Box, Button, Paper, TextField, Typography, Slider, Tooltip } from '@mui/material';
import axios from 'axios';

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

interface QueryResponse {
  primary_result: string;
  all_results: EmbeddingResult[];
}

interface Props {
  paramSet: string;
  onResultSelect: (result: EmbeddingResult) => void;
}

export const QuerySection = ({ paramSet, onResultSelect }: Props) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EmbeddingResult[]>([]);
  const [selected, setSelected] = useState(0);
  const [numResults, setNumResults] = useState(5); // Default to 5 results

  const runQuery = async () => {
    if (!query.trim()) return;

    const res = await axios.post<QueryResponse>('http://localhost:8000/api/query', {
      query,
      params_name: paramSet,
      top_k: numResults, // Override the parameter set's top_k with user selection
    });
    setResults(res.data.all_results);
    if (res.data.all_results.length > 0) {
      const first = res.data.all_results[0];
      setSelected(0);
      onResultSelect(first);
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
        label="Keyword Query"
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
        disabled={!query.trim()}
      >
        Search
      </Button>

      {results.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ mb: 1 }}>
            Search Results ({results.length})
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
                title={r.text}
                placement="top"
                arrow
                enterDelay={500}
                leaveDelay={200}
              >
                <Typography variant="body2" sx={{ mt: 0.5, fontWeight: idx === selected ? 'medium' : 'normal' }}>
                  {r.text.slice(0, 150)}{r.text.length > 150 ? '...' : ''}
                </Typography>
              </Tooltip>
            </Paper>
          ))}
        </Box>
      )}
    </Box>
  );
};
