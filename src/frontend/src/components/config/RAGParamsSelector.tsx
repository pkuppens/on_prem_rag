import { useEffect, useState } from 'react';
import { Box, FormControl, InputLabel, MenuItem, Select, Typography, CircularProgress, Tooltip } from '@mui/material';
import axios from 'axios';
import { apiUrls } from '../../config/api';
import { useBackendStatus } from '../../hooks/useBackendStatus';
import { enhanceErrorMessage } from '../../utils/errorUtils';

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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isBackendRunning, isChecking } = useBackendStatus();

  const fetchSets = async () => {
    try {
      setIsLoading(true);
      const res = await axios.get<SetsResponse>(apiUrls.parameterSets());
      setSets(res.data.sets);

      // If no value is set yet, use the default from the backend
      if (!value) {
        onChange(res.data.default);
      }
      setError(null);
    } catch (err) {
      const originalError = 'Failed to load parameter sets';
      const enhancedError = enhanceErrorMessage(originalError, isBackendRunning, isChecking);
      setError(enhancedError);
      console.error('Error loading parameter sets:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Only fetch parameter sets on initial mount
  useEffect(() => {
    fetchSets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const params = sets[value] || {};

  // Extract key parameters
  const chunkSize = getNestedValue(params, ['chunking', 'chunk_size']);
  const chunkOverlap = getNestedValue(params, ['chunking', 'chunk_overlap']);
  const embeddingModel = getNestedValue(params, ['embedding', 'model_name']);
  const llmModel = getNestedValue(params, ['llm', 'model_name']);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
        <CircularProgress size={20} />
        <Typography variant="body2" color="text.secondary">
          Loading parameter sets...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mb: 4 }}>
        <Tooltip
          title="Click to retry"
          placement="top"
          arrow
        >
          <Typography
            variant="body2"
            color="error"
            sx={{
              cursor: 'pointer',
              whiteSpace: 'pre-line', // Preserve line breaks for enhanced error messages
              '&:hover': {
                textDecoration: 'underline'
              }
            }}
            onClick={() => {
              setError(null);
              setIsLoading(true);
              // Trigger a re-fetch
              fetchSets();
            }}
          >
            {error}
          </Typography>
        </Tooltip>
      </Box>
    );
  }

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
