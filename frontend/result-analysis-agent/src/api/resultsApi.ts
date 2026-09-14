import type { IngestionResult } from '@/types/result';
import apiClient from './client';

// ─── Results / Upload API ─────────────────────────────────────────────────────

export interface UploadResultsPayload {
  file: File;
  academicYear: string;
  semester: number;
  department: string;
  onUploadProgress?: (percent: number) => void;
}

function mapIngestionResult(raw: any): IngestionResult {
  const d = raw?.data ?? raw ?? {};
  const errors = d.validation_errors ?? d.validationIssues ?? [];
  return {
    status: d.status === 'COMPLETED' ? 'COMPLETED' : d.status === 'FAILED' ? 'FAILED' : 'COMPLETED',
    uploadId: String(d.id ?? d.uploadId ?? ''),
    fileName: d.filename ?? d.fileName ?? '',
    uploadedAt: d.created_at ?? d.uploadedAt ?? new Date().toISOString(),
    recordsReceived: d.total_rows ?? d.recordsReceived ?? 0,
    recordsAccepted: d.valid_rows ?? d.recordsAccepted ?? 0,
    recordsRejected: d.rejected_rows ?? d.recordsRejected ?? 0,
    studentsIdentified: d.student_count ?? d.studentsIdentified ?? 0,
    coursesIdentified: d.course_count ?? d.coursesIdentified ?? 0,
    validationIssues: errors.map((v: any) => ({
      severity: v.severity ?? 'ERROR',
      code: v.error_code ?? v.code ?? 'VALIDATION_ERROR',
      message: v.message ?? '',
      affectedRows: v.row_number != null ? [v.row_number] : (v.affectedRows ?? []),
      affectedColumns: v.column_name ? [v.column_name] : (v.affectedColumns ?? []),
      count: 1,
    })),
    errorCount: d.rejected_rows ?? errors.filter((v: any) => v.severity === 'ERROR').length,
    warningCount: errors.filter((v: any) => v.severity === 'WARNING').length,
  };
}

/**
 * POST /api/results/upload
 * Uploads a result file (XLSX / XLS / CSV) and returns the ingestion result.
 */
export async function uploadResults(payload: UploadResultsPayload): Promise<IngestionResult> {
  const formData = new FormData();
  formData.append('file', payload.file);
  formData.append('academic_year', payload.academicYear);
  formData.append('semester', String(payload.semester));
  formData.append('department', payload.department);

  const response = await apiClient.post('/api/results/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (event) => {
      if (event.total && payload.onUploadProgress) {
        const percent = Math.round((event.loaded * 100) / event.total);
        payload.onUploadProgress(percent);
      }
    },
  });

  return mapIngestionResult(response.data);
}

/**
 * GET /api/results/uploads
 * Returns list of recent upload jobs.
 */
export async function getUploadHistory(): Promise<IngestionResult[]> {
  const response = await apiClient.get<any>('/api/results/uploads');
  const list = response.data?.data ?? response.data ?? [];
  return list.map(mapIngestionResult);
}

/**
 * GET /api/results/uploads/:uploadId
 * Returns status of a specific upload.
 */
export async function getUploadStatus(uploadId: string): Promise<IngestionResult> {
  const response = await apiClient.get<any>(`/api/results/uploads/${uploadId}`);
  return mapIngestionResult(response.data);
}
