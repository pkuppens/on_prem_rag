import { useState, useEffect } from 'react';
import { Container, Box } from '@mui/material';
import { FileDropzone } from '../components/upload/FileDropzone';
import { UploadProgress } from '../components/upload/UploadProgress';
import axios from 'axios';
import Logger from '../utils/logger';
import { apiUrls } from '../config/api';

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
  const [paramSet, setParamSet] = useState<string>('default');
  const [pingInterval, setPingInterval] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket(apiUrls.uploadProgressWebSocket());

    websocket.onopen = () => {
      Logger.info(
        'WebSocket connection established',
        'UploadPage.tsx',
        'useEffect',
        20
      );

      // Start sending pings every 30 seconds to keep connection alive
      const interval = setInterval(() => {
        if (websocket.readyState === WebSocket.OPEN) {
          websocket.send('ping');
        }
      }, 30000);

      // Store interval ID for cleanup
      setPingInterval(interval);
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
        [data.file_id]: {
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
      // Clear ping interval
      if (pingInterval) {
        clearInterval(pingInterval);
      }
    };

    setWs(websocket);

    return () => {
      // Clear ping interval
      if (pingInterval) {
        clearInterval(pingInterval);
      }
      websocket.close();
    };
  }, [pingInterval]);

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
          apiUrls.upload(paramSet),
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
