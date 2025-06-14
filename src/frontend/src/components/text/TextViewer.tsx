import { useCallback } from 'react';
import { Box, Typography, Paper, Button } from '@mui/material';
import Logger from '../../utils/logger';

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

interface Props {
  selectedResult: EmbeddingResult | null;
}

export const TextViewer = ({ selectedResult }: Props) => {
  const handleCopy = useCallback(() => {
    const selectedText = window.getSelection()?.toString();
    const textToCopy = selectedText?.trim() ? selectedText : selectedResult?.text;
    if (!textToCopy) return;
    navigator.clipboard.writeText(textToCopy).catch((err) => {
      Logger.error('Copy failed', 'TextViewer.tsx', 'handleCopy', 21, { err });
    });
  }, [selectedResult]);

  if (!selectedResult) {
    return (
      <Paper sx={{ p: 4, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Select a search result to view the text content
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 2, height: 'fit-content' }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" noWrap>
          {selectedResult.document_name}
        </Typography>
        <Button onClick={handleCopy} size="small" variant="outlined">
          Copy Text
        </Button>
      </Box>
      <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'auto', maxHeight: '80vh' }}>
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
          {selectedResult.text || 'No text content available'}
        </Typography>
      </Box>
    </Paper>
  );
};
