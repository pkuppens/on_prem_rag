import { useState, useEffect } from 'react';
import { Container, Typography, Box } from '@mui/material';
import { FileDropzone } from '../components/upload/FileDropzone';
import { UploadProgress } from '../components/upload/UploadProgress';
import { RAGParamsSelector } from '../components/config/RAGParamsSelector';
import axios from 'axios';
import Logger from '../utils/logger';

interface UploadProgress {
  [key: string]: number;
}

export const UploadPage = () => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [paramSet, setParamSet] = useState<string>('');

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8000/ws/upload-progress');

    websocket.onopen = () => {
      Logger.info(
        'WebSocket connection established',
        'UploadPage.tsx',
        'useEffect',
        20
      );
    };

    websocket.onmessage = (event) => {
      const progress = JSON.parse(event.data);
      Logger.debug(
        'Received progress update',
        'UploadPage.tsx',
        'useEffect.onmessage',
        27,
        progress
      );
      setUploadProgress(progress);
    };

    websocket.onerror = (error) => {
      Logger.error(
        'WebSocket error occurred',
        'UploadPage.tsx',
        'useEffect.onerror',
        35,
        error
      );
    };

    websocket.onclose = () => {
      Logger.info(
        'WebSocket connection closed',
        'UploadPage.tsx',
        'useEffect.onclose',
        42
      );
    };

    setWs(websocket);

    return () => {
      websocket.close();
    };
  }, []);

  const handleFileSelect = async (files: File[]) => {
    for (const file of files) {
      Logger.info(
        'Starting file upload',
        'UploadPage.tsx',
        'handleFileSelect',
        55,
        { filename: file.name, size: file.size, type: file.type }
      );

      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await axios.post(
          `http://localhost:8000/api/documents/upload?params_name=${paramSet}`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        Logger.info(
          'File upload completed',
          'UploadPage.tsx',
          'handleFileSelect',
          70,
          response.data
        );
      } catch (error) {
        Logger.error(
          'Error uploading file',
          'UploadPage.tsx',
          'handleFileSelect',
          77,
          error
        );
      }
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Document Upload
      </Typography>

      <RAGParamsSelector value={paramSet} onChange={setParamSet} />

      <Box sx={{ mb: 4 }}>
        <FileDropzone onFileSelect={handleFileSelect} />
      </Box>

      <Box>
        {Object.entries(uploadProgress).map(([filename, progress]) => (
          <UploadProgress
            key={filename}
            filename={filename}
            progress={progress}
          />
        ))}
      </Box>
    </Container>
  );
};
