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

export const RAGParamsSelector = ({ value, onChange }: Props) => {
  const [sets, setSets] = useState<Record<string, unknown>>({});

  useEffect(() => {
    axios.get<SetsResponse>('http://localhost:8000/api/parameters/sets').then((res) => {
      setSets(res.data.sets);
      if (!value) {
        onChange(res.data.default);
      }
    });
  }, []);

  const params = sets[value] || {};

  return (
    <Box sx={{ mb: 4 }}>
      <FormControl fullWidth>
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
        <Typography variant="subtitle2">Selected Parameters</Typography>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{JSON.stringify(params, null, 2)}</pre>
      </Box>
    </Box>
  );
};
