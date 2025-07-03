import { useEffect, useState } from 'react';
import { Box, LinearProgress, Typography, Paper, Fade } from '@mui/material';

/**
 * Props for the UploadProgress component
 * @property {string} filename - Name of the file being uploaded
 * @property {number} progress - Upload progress percentage (0-100)
 * @property {string} [error] - Optional error message from the backend
 * @property {boolean} [isComplete] - Whether the upload has completed successfully
 * @property {() => void} [onComplete] - Callback function when upload completes
 */
interface UploadProgressProps {
  filename: string;
  progress: number;
  error?: string;
  isComplete?: boolean;
  onComplete?: () => void;
}

/**
 * UploadProgress Component
 *
 * A Material-UI based component that displays file upload progress with error handling
 * and completion animations. Uses Paper component for elevation and visual separation.
 *
 * Features:
 * - Progress bar with percentage display
 * - Error state display in red
 * - Success animation (3 green flashes)
 * - Auto-hide after completion
 *
 * Usage example:
 * ```tsx
 * <UploadProgress
 *   filename="example.pdf"
 *   progress={uploadProgress}
 *   error={uploadError}
 *   isComplete={isUploadComplete}
 *   onComplete={() => handleUploadComplete()}
 * />
 * ```
 */
export const UploadProgress = ({
  filename,
  progress,
  error,
  isComplete = false,
  onComplete
}: UploadProgressProps) => {
  // State for managing completion animation
  const [showFlash, setShowFlash] = useState(false);
  const [flashCount, setFlashCount] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  // Validate and sanitize progress value
  const validProgress = typeof progress === 'number' && !isNaN(progress)
    ? Math.max(0, Math.min(100, progress))
    : 0;

  // Handle completion animation sequence
  useEffect(() => {
    if (isComplete && flashCount < 3) {
      const flashInterval = setInterval(() => {
        setShowFlash(prev => !prev);
        setFlashCount(prev => prev + 1);
      }, 500);

      return () => clearInterval(flashInterval);
    }
  }, [isComplete, flashCount]);

  // Handle auto-hide after completion
  useEffect(() => {
    if (isComplete && flashCount >= 3) {
      const hideTimeout = setTimeout(() => {
        setIsVisible(false);
        onComplete?.();
      }, 500);

      return () => clearTimeout(hideTimeout);
    }
  }, [isComplete, flashCount, onComplete]);

  if (!isVisible) return null;

  return (
    <Fade in={isVisible}>
      <Paper
        sx={{
          p: 2,
          mb: 2,
          backgroundColor: showFlash
            ? (error ? 'error.light' : 'rgba(76, 175, 80, 0.1)') // Light green with transparency
            : 'background.paper',
          transition: 'background-color 0.5s ease',
          boxShadow: showFlash && !error
            ? '0 0 8px rgba(76, 175, 80, 0.3)' // Subtle green glow
            : 'none',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography
            variant="body2"
            sx={{
              flexGrow: 1,
              color: error ? 'error.main' : 'text.primary'
            }}
          >
            {filename}
          </Typography>
          <Typography
            variant="body2"
            color={error ? 'error.main' : 'text.secondary'}
          >
            {validProgress}%
          </Typography>
        </Box>
        <LinearProgress
          variant="determinate"
          value={validProgress}
          color={error ? 'error' : 'primary'}
        />
        {error && (
          <Typography
            variant="caption"
            color="error"
            sx={{
              mt: 1,
              display: 'block',
              whiteSpace: 'pre-line' // Preserve line breaks for enhanced error messages
            }}
          >
            {error}
          </Typography>
        )}
      </Paper>
    </Fade>
  );
};
