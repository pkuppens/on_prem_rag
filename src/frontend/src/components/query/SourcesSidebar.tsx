/**
 * Sources sidebar showing retrieved chunks with document name, page, relevance score, and text preview.
 * Used alongside DocumentPreview in the main content area.
 * Issue #84: Polish web UI.
 */

import { Box, Paper, Typography, Tooltip } from '@mui/material';

export interface SourceItem {
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
  sources: SourceItem[];
  selectedIndex: number;
  onSourceSelect: (index: number, source: SourceItem) => void;
  /** Optional max height for scrollable list */
  maxHeight?: number | string;
}

export const SourcesSidebar = ({
  sources,
  selectedIndex,
  onSourceSelect,
  maxHeight = 400,
}: Props) => {
  if (sources.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle2" color="text.secondary">
          Sources
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          No sources yet. Ask a question to see results.
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="subtitle2" sx={{ mb: 1.5, color: 'text.secondary' }}>
        Sources ({sources.length})
      </Typography>
      <Box sx={{ overflow: 'auto', maxHeight, flex: 1 }}>
        {sources.map((r, idx) => (
          <Paper
            key={idx}
            id={`source-${idx}`}
            onClick={() => onSourceSelect(idx, r)}
            sx={{
              p: 1.5,
              mb: 1,
              minHeight: 56,
              cursor: 'pointer',
              bgcolor: idx === selectedIndex ? 'action.selected' : undefined,
              '&:hover': {
                bgcolor: idx === selectedIndex ? 'action.selected' : 'action.hover',
              },
            }}
          >
            <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary' }}>
              {r.document_name} • Page{' '}
              {r.page_number === 'unknown' || r.page_number === undefined
                ? 'N/A'
                : r.page_label &&
                    r.page_label !== 'unknown' &&
                    r.page_label !== String(r.page_number)
                  ? `${r.page_number} (${r.page_label})`
                  : r.page_number}{' '}
              • Score: {r.similarity_score.toFixed(3)}
            </Typography>
            <Tooltip title={r.text || 'No text content available'} placement="top" arrow enterDelay={500} leaveDelay={200}>
              <Typography variant="body2" sx={{ mt: 0.5, fontWeight: idx === selectedIndex ? 'medium' : 'normal' }}>
                {r.text ? `${r.text.slice(0, 150)}${r.text.length > 150 ? '...' : ''}` : 'No text content available'}
              </Typography>
            </Tooltip>
          </Paper>
        ))}
      </Box>
    </Box>
  );
};
