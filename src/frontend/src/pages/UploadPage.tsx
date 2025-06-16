import { useState, useEffect } from 'react';
import { Container, Box } from '@mui/material';
import { FileDropzone } from '../components/upload/FileDropzone';
import { UploadProgress } from '../components/upload/UploadProgress';
import axios from 'axios';
import Logger from '../utils/logger';

interface UploadProgress {
  [key: string]: {
    progress: number;
    error?: string;
    isComplete?: boolean;
  };
}

export const UploadPage = () => {
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({});
  const [ws, setWs] = useState<WebSocket | null>(null);

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
      const data = JSON.parse(event.data);
      Logger.debug(
        'Received progress update',
        'UploadPage.tsx',
        'useEffect.onmessage',
        27,
        data
      );
      setUploadProgress(prev => ({
        ...prev,
        [data.filename]: {
          progress: data.progress,
          error: data.error,
          isComplete: data.isComplete
        }
      }));
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

        // Mark upload as complete
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: {
            ...prev[file.name],
            progress: 100,
            isComplete: true
          }
        }));
      } catch (error) {
        Logger.error(
          'Error uploading file',
          'UploadPage.tsx',
          'handleFileSelect',
          77,
          error
        );

        // Set error state
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: {
            ...prev[file.name],
            error: error instanceof Error ? error.message : 'Upload failed'
          }
        }));
      }
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <FileDropzone onFileSelect={handleFileSelect} />
      </Box>

      <Box>
        {Object.entries(uploadProgress).map(([filename, data]) => (
          <UploadProgress
            key={filename}
            filename={filename}
            progress={data.progress}
            error={data.error}
            isComplete={data.isComplete}
            onComplete={() => {
              // Remove the completed upload from the progress list
              setUploadProgress(prev => {
                const newProgress = { ...prev };
                delete newProgress[filename];
                return newProgress;
              });
            }}
          />
        ))}
      </Box>
    </Container>
  );
};
