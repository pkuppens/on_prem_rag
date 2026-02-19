import { useCallback } from 'react';
import { Box, Typography, Paper, Button, CircularProgress } from '@mui/material';
import Logger from '../../utils/logger';
import { useDocumentTextContent } from '../../hooks/useDocumentTextContent';

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
  /** If true, fetch full file content via as-text; otherwise show chunk snippet only */
  fetchFullFile?: boolean;
}

export const TextViewer = ({ selectedResult, fetchFullFile = true }: Props) => {
  const { content, loading, error } = useDocumentTextContent(
    selectedResult?.document_name ?? null,
    !!selectedResult && fetchFullFile
  );

  const displayText = content ?? selectedResult?.text ?? '';
  const handleCopy = useCallback(() => {
    const selectedText = window.getSelection()?.toString();
    const textToCopy = selectedText?.trim() ? selectedText : displayText;
    if (!textToCopy) return;
    navigator.clipboard.writeText(textToCopy).catch((err) => {
      Logger.error('Copy failed', 'TextViewer.tsx', 'handleCopy', 21, { err });
    });
  }, [displayText]);

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
        <Button onClick={handleCopy} size="small" variant="outlined" disabled={loading || !!error}>
          Copy Text
        </Button>
      </Box>
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress size={24} />
        </Box>
      )}
      {error && (
        <Typography variant="body2" color="error" sx={{ mb: 2 }}>
          {error}
        </Typography>
      )}
      <Box sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'auto', maxHeight: '80vh' }}>
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
          {loading ? '' : displayText || 'No text content available'}
        </Typography>
      </Box>
    </Paper>
  );
};
