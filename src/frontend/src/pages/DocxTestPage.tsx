import { Container, Typography, Paper } from '@mui/material';
import { DOCXViewer } from '../components/docx/DOCXViewer';

const SAMPLE_DOCX = 'http://localhost:8000/files/toolsfairy-com-sample-docx-files-sample4.docx';

export const DocxTestPage = () => (
  <Container maxWidth="md" sx={{ py: 4 }}>
    <Typography variant="h4" gutterBottom>DOCX Viewer Test</Typography>
    <Paper sx={{ p: 2 }}>
      <DOCXViewer selectedResult={{
        text: 'Sample DOCX content',
        similarity_score: 1,
        document_id: 'docx',
        document_name: 'toolsfairy-com-sample-docx-files-sample4.docx',
        chunk_index: 0,
        record_id: '1',
        page_number: 1,
      }} />
    </Paper>
  </Container>
);
export default DocxTestPage;
