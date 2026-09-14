// Recharts formatter type helper

export type Grade = 'A+' | 'A' | 'B+' | 'B' | 'C' | 'D' | 'F' | string;

export type PassFailStatus = 'PASS' | 'FAIL' | 'ABSENT' | 'WITHHELD';

export interface StudentResult {
  rollNumber: string;
  studentName: string;
  programme: string;
  branch: string;
  section: string;
  semester: number;
  academicYear: string;
  courseCode: string;
  courseName: string;
  internalMarks: number | null;
  externalMarks: number | null;
  totalMarks: number | null;
  maxMarks: number;
  grade: Grade;
  gradePoints: number | null;
  credits: number;
  status: PassFailStatus;
}

export interface StudentSummary {
  rollNumber: string;
  studentName: string;
  programme: string;
  branch: string;
  section: string;
  batch: string;
  semester: number;
  academicYear: string;
  sgpa: number | null;
  cgpa: number | null;
  totalCredits: number;
  earnedCredits: number;
  backlogs: number;
  status: PassFailStatus;
}

// ─── Upload / Ingestion ───────────────────────────────────────────────────────

export type IngestionStatus =
  | 'IDLE'
  | 'UPLOADING'
  | 'VALIDATING'
  | 'RECONCILING'
  | 'ANALYZING'
  | 'COMPLETED'
  | 'FAILED';

export type ValidationSeverity = 'ERROR' | 'WARNING' | 'INFO';

export interface ValidationIssue {
  severity: ValidationSeverity;
  code: string;
  message: string;
  affectedRows: number[];
  affectedColumns: string[];
  count: number;
}

export interface IngestionResult {
  status: IngestionStatus;
  uploadId: string;
  fileName: string;
  uploadedAt: string;
  recordsReceived: number;
  recordsAccepted: number;
  recordsRejected: number;
  studentsIdentified: number;
  coursesIdentified: number;
  validationIssues: ValidationIssue[];
  errorCount: number;
  warningCount: number;
}

export interface UploadProgress {
  status: IngestionStatus;
  percent: number;
  message: string;
}

// ─── Filters ─────────────────────────────────────────────────────────────────

export interface ResultFilters {
  academicYear?: string;
  semester?: number;
  department?: string;
  programme?: string;
  batch?: string;
  section?: string;
  courseCode?: string;
}
