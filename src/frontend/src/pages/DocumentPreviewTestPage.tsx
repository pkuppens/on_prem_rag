/**
 * Standalone tester page for document preview.
 *
 * Switch between .pdf, .txt, .md, .docx to verify the correct viewer is selected
 * and that content loads (requires backend and uploaded files).
 *
 * Access via: ?test=preview
 */

import { useState } from 'react';
import { Box, Container, FormControl, InputLabel, MenuItem, Paper, Select, Typography } from '@mui/material';
import { DocumentPreview } from '../components/preview/DocumentPreview';
import { hasPreview } from '../config/documentPreview';

type FileType = 'pdf' | 'txt' | 'md' | 'docx';

const SAMPLE_FILES: Record<FileType, string> = {
  pdf: 'sample.pdf',
  txt: 'metformin_timing_test.txt',
  md: 'README.md',
  docx: 'sample.docx',
};

const MOCK_RESULT = (document_name: string, text: string) => ({
  text,
  similarity_score: 0.95,
  document_id: document_name,
  document_name,
  chunk_index: 0,
  record_id: '1',
  page_number: 1,
});

export const DocumentPreviewTestPage = () => {
  const [fileType, setFileType] = useState<FileType>('txt');
  const filename = SAMPLE_FILES[fileType];
  const selectedResult = MOCK_RESULT(
    filename,
    fileType === 'txt'
      ? 'Metformin timing test content...'
      : fileType === 'md'
        ? '# Markdown sample\n\nBody text...'
        : fileType === 'docx'
          ? 'DOCX extracted content...'
          : 'PDF chunk preview...'
  );

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Document Preview Tester
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Switch file type to verify the correct viewer (PDF, Text, DOCX) is selected. Content loads from backend when the
        file exists in uploaded documents.
      </Typography>

      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap' }}>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>File Type</InputLabel>
          <Select
            value={fileType}
            label="File Type"
            onChange={(e) => setFileType(e.target.value as FileType)}
          >
            <MenuItem value="pdf">PDF</MenuItem>
            <MenuItem value="txt">TXT</MenuItem>
            <MenuItem value="md">Markdown</MenuItem>
            <MenuItem value="docx">DOCX</MenuItem>
          </Select>
        </FormControl>
        <Paper sx={{ p: 2, alignSelf: 'flex-start' }}>
          <Typography variant="caption" color="text.secondary">
            Preview: {hasPreview(filename) ? filename : 'not supported'}
          </Typography>
        </Paper>
      </Box>

      <Paper sx={{ mt: 3, p: 2, minHeight: 400 }}>
        <DocumentPreview selectedResult={selectedResult} />
      </Paper>
    </Container>
  );
};

export default DocumentPreviewTestPage;
