import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Typography, Paper } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

interface FileDropzoneProps {
  onFileSelect: (files: File[]) => void;
}

export const FileDropzone = ({ onFileSelect }: FileDropzoneProps) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      onFileSelect(acceptedFiles);
    },
    [onFileSelect]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
  });

  return (
    <Paper
      {...getRootProps()}
      sx={{
        p: 3,
        textAlign: 'center',
        cursor: 'pointer',
        bgcolor: isDragActive ? 'action.hover' : 'background.paper',
        border: '2px dashed',
        borderColor: isDragActive ? 'primary.main' : 'divider',
      }}
    >
      <input {...getInputProps()} />
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main' }} />
        <Typography variant="h6">
          {isDragActive
            ? 'Drop the files here'
            : 'Drag and drop files here, or click to select files'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Supported formats: PDF, DOCX, TXT
        </Typography>
      </Box>
    </Paper>
  );
};
