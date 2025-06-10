import { useEffect, useState } from 'react';
import { Box, FormControl, InputLabel, MenuItem, Select, Typography } from '@mui/material';
import axios from 'axios';

interface Props {
  value: string;
  onChange: (val: string) => void;
}

interface SetsResponse {
  default: string;
  sets: Record<string, unknown>;
}

// Helper function to safely get nested values
const getNestedValue = (obj: any, path: string[]): any => {
  return path.reduce((acc, part) => (acc && acc[part] !== undefined ? acc[part] : null), obj);
};

export const RAGParamsSelector = ({ value, onChange }: Props) => {
  const [sets, setSets] = useState<Record<string, unknown>>({});

  useEffect(() => {
    axios.get<SetsResponse>('http://localhost:8000/api/parameters/sets').then((res) => {
      setSets(res.data.sets);
      // If no value is set yet, try to use 'fast' first, then default
      if (!value) {
        const preferredDefault = Object.keys(res.data.sets).includes('fast')
          ? 'fast'
          : res.data.default;
        onChange(preferredDefault);
      }
    });
  }, [value, onChange]);

  const params = sets[value] || {};

  // Extract key parameters
  const chunkSize = getNestedValue(params, ['chunking', 'chunk_size']);
  const chunkOverlap = getNestedValue(params, ['chunking', 'chunk_overlap']);
  const embeddingModel = getNestedValue(params, ['embedding', 'model_name']);
  const llmModel = getNestedValue(params, ['llm', 'model_name']);

  return (
    <Box sx={{ mb: 4 }}>
      <FormControl fullWidth size="medium">
        <InputLabel id="rag-set-label">RAG Parameter Set</InputLabel>
        <Select
          labelId="rag-set-label"
          label="RAG Parameter Set"
          value={value}
          onChange={(e) => onChange(e.target.value as string)}
        >
          {Object.keys(sets).map((name) => (
            <MenuItem key={name} value={name}>
              {name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Box sx={{ mt: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>Selected Parameters</Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
          {chunkSize && chunkOverlap && (
            <Typography variant="body2" color="text.secondary">
              Chunk Size/Overlap: {chunkSize} / {chunkOverlap}
            </Typography>
          )}
          {embeddingModel && (
            <Typography variant="body2" color="text.secondary">
              Embedding: {embeddingModel}
            </Typography>
          )}
          {llmModel && (
            <Typography variant="body2" color="text.secondary">
              LLM: {llmModel}
            </Typography>
          )}
        </Box>
      </Box>
    </Box>
  );
};
