import type { ReportJob, ReportRequest, ReportStatus, ReportType, ReportFormat } from '@/types/report';
import apiClient from './client';

function unwrap<T>(data: any): T {
  if (data && typeof data === 'object' && 'data' in data) {
    return data.data;
  }
  return data;
}

export function mapReportJob(raw: any): ReportJob {
  const data = unwrap<any>(raw) ?? {};
  const statusStr = String(data.status ?? '').toUpperCase();
  let status: ReportStatus = 'IDLE';
  if (statusStr === 'COMPLETED' || statusStr === 'READY') {
    status = 'READY';
  } else if (statusStr === 'RUNNING' || statusStr === 'GENERATING') {
    status = 'GENERATING';
  } else if (statusStr === 'PENDING' || statusStr === 'PREPARING') {
    status = 'PREPARING';
  } else if (statusStr === 'FAILED') {
    status = 'FAILED';
  }

  const jobId = String(data.id ?? data.jobId ?? '');
  const downloadUrl = data.download_url ?? data.downloadUrl ?? (jobId ? `/api/reports/${jobId}/download` : null);

  return {
    jobId,
    reportType: (data.run_type ?? data.reportType ?? 'SEMESTER_SUMMARY') as ReportType,
    status,
    requestedAt: data.created_at ?? data.requestedAt ?? new Date().toISOString(),
    completedAt: data.completed_at ?? data.completedAt ?? null,
    downloadUrl,
    fileName: data.report_path ? String(data.report_path).split(/[\/\\]/).pop() ?? null : null,
    errorMessage: data.error_message ?? data.errorMessage ?? null,
    parameters: {
      academicYear: data.academic_year ?? data.parameters?.academicYear ?? '',
      semester: data.semester ?? data.parameters?.semester ?? 1,
      department: data.department ?? data.parameters?.department ?? undefined,
      format: (data.report_format ?? data.parameters?.format ?? 'PDF') as ReportFormat,
    },
  };
}

// ─── Reports API ──────────────────────────────────────────────────────────────

/**
 * POST /api/reports/generate
 * Initiates a report generation job and returns the job record.
 */
export async function generateReport(request: ReportRequest): Promise<ReportJob> {
  const params = {
    academic_year: request.academicYear,
    semester: String(request.semester),
    department: request.department || 'All Departments',
    report_type: request.reportType,
    format: request.format,
  };
  const response = await apiClient.post<any>('/api/reports/generate', null, { params });
  return mapReportJob(response.data);
}

/**
 * GET /api/reports/:jobId
 * Polls the status of a report generation job.
 */
export async function getReportJob(jobId: string): Promise<ReportJob> {
  const response = await apiClient.get<any>(`/api/reports/${jobId}`);
  return mapReportJob(response.data);
}

/**
 * GET /api/reports/jobs
 * Returns the list of recent report jobs for the current user / department.
 */
export async function getReportJobs(): Promise<ReportJob[]> {
  const response = await apiClient.get<any>('/api/reports/jobs');
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map(mapReportJob);
}

/**
 * Download generated report file directly with authentication.
 */
export async function downloadReportFile(jobId: string, fileName?: string): Promise<void> {
  const response = await apiClient.get(`/api/reports/${jobId}/download`, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fileName || `report_${jobId}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function getReportDownloadUrl(jobId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/reports/${jobId}/download`;
}
