/**
 * Voice input button for recording audio and transcribing to text.
 *
 * Uses MediaRecorder to capture audio, then POSTs to /api/stt/transcribe/draft.
 * Satisfies AC-3: mic control, calls STT API, record → transcribe → display.
 */

import { useState, useRef, useCallback } from 'react';
import { IconButton, Tooltip, CircularProgress } from '@mui/material';
import MicIcon from '@mui/icons-material/Mic';
import MicOffIcon from '@mui/icons-material/MicOff';
import axios from 'axios';
import { apiUrls } from '../../config/api';

interface Props {
  /** Called when transcription is received */
  onTranscription: (text: string) => void;
  /** Called on error */
  onError?: (message: string) => void;
  disabled?: boolean;
}

export const VoiceInputButton = ({ onTranscription, onError, disabled }: Props) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const stopRecording = useCallback(() => {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') {
      mr.stop();
    }
    mediaRecorderRef.current = null;
    setIsRecording(false);
  }, []);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm';
      const recorder = new MediaRecorder(stream);

      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const ext = mimeType.includes('webm') ? '.webm' : '.wav';

        setIsTranscribing(true);
        try {
          const formData = new FormData();
          formData.append('audio', blob, `recording${ext}`);
          formData.append('language', '');

          const res = await axios.post(apiUrls.sttTranscribeDraft(), formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 30000,
          });

          const text = (res.data?.text || '').trim();
          if (text) {
            onTranscription(text);
          } else {
            onError?.('No speech detected. Try again.');
          }
        } catch (err) {
          const msg = axios.isAxiosError(err)
            ? err.response?.data?.detail || err.message
            : 'Transcription failed';
          onError?.(msg);
        } finally {
          setIsTranscribing(false);
        }
      };

      recorder.start();
      mediaRecorderRef.current = recorder;
      setIsRecording(true);
    } catch (err) {
      onError?.('Microphone access denied or not available.');
    }
  }, [onTranscription, onError]);

  const handleClick = useCallback(() => {
    if (disabled || isTranscribing) return;
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [disabled, isTranscribing, isRecording, startRecording, stopRecording]);

  const label = isTranscribing
    ? 'Transcribing...'
    : isRecording
      ? 'Stop recording'
      : 'Start voice input';

  return (
    <Tooltip title={label}>
      <span>
        <IconButton
          onClick={handleClick}
          disabled={disabled || isTranscribing}
          color={isRecording ? 'error' : 'default'}
          aria-label={label}
        >
          {isTranscribing ? (
            <CircularProgress size={24} />
          ) : isRecording ? (
            <MicOffIcon />
          ) : (
            <MicIcon />
          )}
        </IconButton>
      </span>
    </Tooltip>
  );
};
