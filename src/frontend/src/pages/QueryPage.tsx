import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Grid,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import { Document as PDFDocument, Page } from 'react-pdf';
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

interface QueryResponse {
  primary_result: string;
  all_results: EmbeddingResult[];
}

export const QueryPage = () => {
  const [paramSet, setParamSet] = useState('fast');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<EmbeddingResult[]>([]);
  const [selected, setSelected] = useState(0);
  const [page, setPage] = useState(1);

  const runQuery = async () => {
    const res = await axios.post<QueryResponse>('http://localhost:8000/api/query', {
      query,
      params_name: paramSet,
    });
    setResults(res.data.all_results);
    if (res.data.all_results.length > 0) {
      const first = res.data.all_results[0];
      setSelected(0);
      setPage(Number(first.page_number) || 1);
    }
  };

  const selectedResult = results[selected];
  const pdfUrl = selectedResult
    ? `http://localhost:8000/files/${selectedResult.document_name}`
    : '';

  return (
    <Grid container spacing={2} sx={{ p: 2 }}>
      <Grid item xs={12} md={4}>
        <Box sx={{ mb: 2 }}>
          <RAGParamsSelector value={paramSet} onChange={setParamSet} />
        </Box>
        <TextField
          fullWidth
          label="Keyword Query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          sx={{ mb: 2 }}
          size="medium"
          variant="outlined"
        />
        <Button variant="contained" fullWidth onClick={runQuery} sx={{ mb: 2 }}>
          Search
        </Button>
        {results.map((r, idx) => (
          <Paper
            key={idx}
            onClick={() => {
              setSelected(idx);
              setPage(Number(r.page_number) || 1);
            }}
            sx={{
              p: 1,
              mb: 1,
              cursor: 'pointer',
              bgcolor: idx === selected ? 'action.hover' : undefined,
            }}
          >
            <Typography variant="caption" sx={{ display: 'block' }}>
              p.{r.page_number}
            </Typography>
            <Typography variant="body2" noWrap>
              {r.text.slice(0, 100)}
            </Typography>
          </Paper>
        ))}
      </Grid>
      <Grid item xs={12} md={8}>
        {selectedResult && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Button onClick={() => setPage((p) => Math.max(1, p - 1))}>Prev</Button>
              <Typography>Page {page}</Typography>
              <Button onClick={() => setPage((p) => p + 1)}>Next</Button>
            </Box>
            <PDFDocument file={pdfUrl}>
              <Page pageNumber={page} width={800} />
            </PDFDocument>
          </Box>
        )}
      </Grid>
    </Grid>
  );
};
