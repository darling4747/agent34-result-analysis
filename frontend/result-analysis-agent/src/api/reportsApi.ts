import type { ReportJob, ReportRequest } from '@/types/report';
import apiClient from './client';

// ─── Reports API ──────────────────────────────────────────────────────────────

/**
 * POST /api/reports/generate
 * Initiates a report generation job and returns the job record.
 */
export async function generateReport(request: ReportRequest): Promise<ReportJob> {
  const response = await apiClient.post<ReportJob>('/api/reports/generate', request);
  return response.data;
}

/**
 * GET /api/reports/jobs/:jobId
 * Polls the status of a report generation job.
 */
export async function getReportJob(jobId: string): Promise<ReportJob> {
  const response = await apiClient.get<ReportJob>(`/api/reports/jobs/${jobId}`);
  return response.data;
}

/**
 * GET /api/reports/jobs
 * Returns the list of recent report jobs for the current user / department.
 */
export async function getReportJobs(): Promise<ReportJob[]> {
  const response = await apiClient.get<ReportJob[]>('/api/reports/jobs');
  return response.data;
}

/**
 * GET /api/reports/download/:jobId
 * Returns a signed download URL or initiates a file download.
 * The caller should open this URL in a new tab or trigger a browser download.
 */
export function getReportDownloadUrl(jobId: string): string {
  const base = import.meta.env.VITE_API_BASE_URL ?? '';
  return `${base}/api/reports/download/${jobId}`;
}
