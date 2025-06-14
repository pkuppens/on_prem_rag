import { Container, Typography, Paper } from '@mui/material';
import { TextViewer } from '../components/text/TextViewer';

export const TextTestPage = () => (
  <Container maxWidth="md" sx={{ py: 4 }}>
    <Typography variant="h4" gutterBottom>Text Viewer Test</Typography>
    <Paper sx={{ p: 2 }}>
      <TextViewer selectedResult={{
        text: 'Example plain text from tests',
        similarity_score: 1,
        document_id: 'txt',
        document_name: 'sample.txt',
        chunk_index: 0,
        record_id: '1',
        page_number: 1,
      }} />
    </Paper>
  </Container>
);
export default TextTestPage;
