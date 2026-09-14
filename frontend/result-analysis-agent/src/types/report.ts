// ─── Report Types ─────────────────────────────────────────────────────────────

export type ReportType =
  | 'SEMESTER_SUMMARY'
  | 'DEPARTMENT'
  | 'COURSE'
  | 'MERIT_LIST'
  | 'INTERVENTION'
  | 'CORRELATION';

export type ReportStatus =
  | 'IDLE'
  | 'PREPARING'
  | 'ANALYZING'
  | 'GENERATING'
  | 'READY'
  | 'FAILED';

export type ReportFormat = 'PDF' | 'EXCEL' | 'PRINT';

export interface ReportRequest {
  reportType: ReportType;
  academicYear: string;
  semester: number;
  department?: string;
  programme?: string;
  courseCode?: string;
  format: ReportFormat;
}

export interface ReportJob {
  jobId: string;
  reportType: ReportType;
  status: ReportStatus;
  requestedAt: string;
  completedAt: string | null;
  downloadUrl: string | null;
  fileName: string | null;
  errorMessage: string | null;
  parameters: Partial<ReportRequest>;
}

export interface ReportOption {
  type: ReportType;
  label: string;
  description: string;
  icon: string;
  requiresCourse: boolean;
  requiresDepartment: boolean;
}
