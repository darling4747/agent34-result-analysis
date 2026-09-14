import { useEffect, useState } from 'react';
import apiClient from '@/api/client';

export interface DatasetInfo {
  has_data: boolean;
  message?: string;
  batch_id?: number | null;
  filename?: string | null;
  academic_year?: string | null;
  semester?: number | null;
  department?: string | null;
  uploaded_at?: string | null;
  student_count: number;
  result_count: number;
  course_count: number;
  status?: string;
  analysis_status?: string;
}

const EMPTY_DATASET: DatasetInfo = {
  has_data: false,
  message: 'No result dataset has been uploaded yet.',
  student_count: 0,
  result_count: 0,
  course_count: 0,
};

export function useDataset(refreshKey = 0) {
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    apiClient.get('/api/results/dataset-info')
      .then((res) => {
        if (!cancelled) {
          setDatasetInfo(res.data.data ?? EMPTY_DATASET);
          setError(null);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setDatasetInfo(EMPTY_DATASET);
          setError(null);
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [tick, refreshKey]);

  return {
    datasetInfo,
    loading,
    error,
    refresh: () => setTick((t) => t + 1),
  };
}
