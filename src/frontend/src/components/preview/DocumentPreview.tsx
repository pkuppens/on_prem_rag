/**
 * Document preview dispatcher - selects the correct viewer by file extension.
 *
 * Routes to PDFViewer, TextViewer, or DOCXViewer based on getPreviewConfig().
 * Supports .pdf, .txt, .md, .docx, .doc.
 */

import { Paper, Typography } from '@mui/material';
import { PDFViewer } from '../pdf/PDFViewer';
import { DOCXViewer } from '../docx/DOCXViewer';
import { TextViewer } from '../text/TextViewer';
import { getPreviewConfig } from '../../config/documentPreview';

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

export const DocumentPreview = ({ selectedResult }: Props) => {
  if (!selectedResult) {
    return (
      <Paper sx={{ p: 4, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Select a search result to view the document
        </Typography>
      </Paper>
    );
  }

  const config = getPreviewConfig(selectedResult.document_name);
  if (!config) {
    return (
      <Paper sx={{ p: 4, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          Preview not available for this file type
        </Typography>
      </Paper>
    );
  }

  switch (config.type) {
    case 'pdf':
      return <PDFViewer selectedResult={selectedResult} />;
    case 'docx-text':
      return <DOCXViewer selectedResult={selectedResult} />;
    case 'text':
    case 'markdown':
      return <TextViewer selectedResult={selectedResult} fetchFullFile={config.fetchAsText} />;
    default:
      return <TextViewer selectedResult={selectedResult} fetchFullFile />;
  }
};
