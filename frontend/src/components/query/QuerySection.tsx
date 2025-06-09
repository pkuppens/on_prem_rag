import { useState } from 'react';
import { Box, Button, Paper, TextField, Typography } from '@mui/material';
import axios from 'axios';

interface EmbeddingResult {
  text: string;
  similarity_score: number;
  document_id: string;
  document_name: string;
  chunk_index: number;
  record_id: string;
  page_number: number | string;
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

  const runQuery = async () => {
    if (!query.trim()) return;

    const res = await axios.post<QueryResponse>('http://localhost:8000/api/query', {
      query,
      params_name: paramSet,
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
                {r.document_name} • Page {r.page_number === 'unknown' || r.page_number === undefined ? 'N/A' : r.page_number} • Chunk {r.chunk_index} • Score: {r.similarity_score.toFixed(3)}
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5, fontWeight: idx === selected ? 'medium' : 'normal' }}>
                {r.text.slice(0, 150)}{r.text.length > 150 ? '...' : ''}
              </Typography>
            </Paper>
          ))}
        </Box>
      )}
    </Box>
  );
};
