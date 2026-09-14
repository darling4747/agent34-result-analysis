import { useCallback, useState } from 'react';
import { generateReport, getReportDownloadUrl, getReportJob } from '@/api/reportsApi';
import type { ReportJob, ReportRequest, ReportStatus } from '@/types/report';
import { ApiError } from '@/api/client';

interface ReportState {
  status: ReportStatus;
  job: ReportJob | null;
  error: string | null;
}

const IDLE: ReportState = { status: 'IDLE', job: null, error: null };

export function useReportGenerator() {
  const [state, setState] = useState<ReportState>(IDLE);

  const generate = useCallback(async (request: ReportRequest) => {
    setState({ status: 'PREPARING', job: null, error: null });
    try {
      let job = await generateReport(request);
      setState({ status: job.status, job, error: null });
      let attempts = 0;
      while (job.status !== 'READY' && job.status !== 'FAILED' && attempts < 30) {
        await new Promise((r) => setTimeout(r, 2000));
        job = await getReportJob(job.jobId);
        setState({ status: job.status, job, error: null });
        attempts++;
      }
      if (job.status === 'FAILED') {
        setState({ status: 'FAILED', job, error: job.errorMessage ?? 'Report generation failed.' });
      }
    } catch (err) {
      const message = err instanceof ApiError ? err.message : 'Failed to generate report.';
      setState({ status: 'FAILED', job: null, error: message });
    }
  }, []);

  const download = useCallback((jobId: string) => {
    window.open(getReportDownloadUrl(jobId), '_blank', 'noopener,noreferrer');
  }, []);

  const reset = useCallback(() => setState(IDLE), []);

  return { ...state, generate, download, reset };
}
