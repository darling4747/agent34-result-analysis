import { useCallback, useState } from 'react';
import { uploadResults } from '@/api/resultsApi';
import type { IngestionResult, IngestionStatus } from '@/types/result';
import { ApiError } from '@/api/client';
import { MAX_FILE_SIZE_BYTES, ACCEPTED_FILE_TYPES } from '@/utils/constants';

interface UploadState {
  status: IngestionStatus;
  percent: number;
  message: string;
  result: IngestionResult | null;
  error: string | null;
}

const IDLE_STATE: UploadState = {
  status: 'IDLE',
  percent: 0,
  message: '',
  result: null,
  error: null,
};

export function useUpload() {
  const [state, setState] = useState<UploadState>(IDLE_STATE);

  const validateFile = useCallback((file: File): string | null => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_FILE_TYPES.includes(ext)) {
      return `Invalid file type. Accepted: ${ACCEPTED_FILE_TYPES.join(', ')}`;
    }
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return 'File exceeds maximum size of 50 MB.';
    }
    return null;
  }, []);

  const upload = useCallback(async (
    file: File,
    academicYear: string,
    semester: number,
    department: string,
  ) => {
    const validationError = validateFile(file);
    if (validationError) {
      setState({ ...IDLE_STATE, status: 'FAILED', error: validationError });
      return;
    }

    setState({ status: 'UPLOADING', percent: 0, message: 'Uploading file…', result: null, error: null });

    try {
      const result = await uploadResults({
        file,
        academicYear,
        semester,
        department,
        onUploadProgress: (percent) => {
          setState((s) => ({
            ...s,
            percent,
            message: percent < 100 ? `Uploading… ${percent}%` : 'Processing…',
          }));
        },
      });
      setState({ status: 'COMPLETED', percent: 100, message: 'Ingestion complete.', result, error: null });
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Upload failed. Please try again.';
      setState({ status: 'FAILED', percent: 0, message, result: null, error: message });
    }
  }, [validateFile]);

  const reset = useCallback(() => setState(IDLE_STATE), []);

  return { ...state, upload, reset, validateFile };
}