import { useEffect, useState } from 'react';
import { Box, LinearProgress, Typography, Paper } from '@mui/material';

interface UploadProgressProps {
  filename: string;
  progress: number;
}

export const UploadProgress = ({ filename, progress }: UploadProgressProps) => {
  return (
    <Paper sx={{ p: 2, mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Typography variant="body2" sx={{ flexGrow: 1 }}>
          {filename}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {progress}%
        </Typography>
      </Box>
      <LinearProgress variant="determinate" value={progress} />
    </Paper>
  );
};
