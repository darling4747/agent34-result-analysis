// ─── Summary / KPIs ───────────────────────────────────────────────────────────

export interface ResultSummary {
  totalStudents: number;
  totalResults: number;
  passCount: number;
  failCount: number;
  passPercentage: number;
  failPercentage: number;
  averageMarks: number;
  averageGpa: number;
  previousPassPercentage: number | null;
  previousAverageMarks: number | null;
  semester: number;
  academicYear: string;
  department: string;
}

// ─── Grade Distribution ───────────────────────────────────────────────────────

export interface GradeDistributionItem {
  grade: string;
  count: number;
  percentage: number;
}

// ─── Course Analysis ──────────────────────────────────────────────────────────

export type PriorityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export interface CourseMetrics {
  courseCode: string;
  courseName: string;
  faculty: string;
  credits: number;
  studentCount: number;
  passCount: number;
  failCount: number;
  passPercentage: number;
  failurePercentage: number;
  averageMarks: number;
  averageGpa: number;
  historicalDeviation: number | null;
  priorityLevel: PriorityLevel;
  gradeDistribution: GradeDistributionItem[];
}

export interface CourseDetail extends CourseMetrics {
  sections: SectionMetrics[];
  internalExternalCorrelation: CorrelationResult | null;
  interventionStatus: PriorityLevel | null;
  analyticalObservations: string[];
  marksDistribution: MarksDistributionItem[];
}

export interface MarksDistributionItem {
  range: string;
  count: number;
}

// ─── Section Analysis ─────────────────────────────────────────────────────────

export interface SectionMetrics {
  section: string;
  programme: string;
  branch: string;
  studentCount: number;
  passCount: number;
  failCount: number;
  passRate: number;
  failureRate: number;
  averageMarks: number;
  averageGpa: number;
  topScore: number | null;
  lowestScore: number | null;
}

// ─── Faculty Analysis ─────────────────────────────────────────────────────────

export interface FacultyMetrics {
  facultyId: string;
  facultyName: string;
  department: string;
  coursesHandled: string[];
  totalStudents: number;
  averageMarks: number;
  passRate: number;
  historicalBaseline: number | null;
  deviation: number | null;
  coursesRequiringReview: string[];
  contextNote: string;
}

// ─── Merit List ───────────────────────────────────────────────────────────────

export type MeritScope = 'PROGRAMME' | 'SECTION' | 'COURSE';

export interface MeritEntry {
  rank: number;
  rollNumber: string;
  studentName: string;
  programme: string;
  branch: string;
  section: string;
  batch: string;
  sgpa: number;
  cgpa: number | null;
  totalMarks: number;
  status: 'DISTINCTION' | 'FIRST_CLASS' | 'SECOND_CLASS' | 'PASS';
  scope: MeritScope;
}

// ─── Internal / External Correlation ─────────────────────────────────────────

export type CorrelationInterpretation =
  | 'STRONG_POSITIVE'
  | 'MODERATE_POSITIVE'
  | 'WEAK_POSITIVE'
  | 'WEAK_NEGATIVE'
  | 'STRONG_NEGATIVE'
  | 'INSUFFICIENT_DATA';

export interface CorrelationResult {
  courseCode: string;
  courseName: string;
  studentCount: number;
  internalAverage: number;
  externalAverage: number;
  pearsonCorrelation: number | null;
  interpretation: CorrelationInterpretation;
  flags: CorrelationFlag[];
  scatterData: ScatterPoint[];
}

export type CorrelationFlag =
  | 'HIGH_INTERNAL_LOW_EXTERNAL'
  | 'LARGE_INTERNAL_EXTERNAL_GAP'
  | 'WEAK_CORRELATION'
  | 'NEGATIVE_CORRELATION';

export interface ScatterPoint {
  rollNumber: string;
  internalMarks: number;
  externalMarks: number;
}

// ─── Historical Analysis ──────────────────────────────────────────────────────

export interface HistoricalDataPoint {
  academicYear: string;
  semester: number;
  label: string;
  passRate: number;
  averageMarks: number;
  averageGpa: number;
  failureRate: number;
  studentCount: number;
}

export interface HistoricalComparison {
  courseCode: string;
  courseName: string;
  currentValue: number;
  previousValue: number | null;
  historicalAverage: number | null;
  deviationFromAverage: number | null;
  trend: 'IMPROVING' | 'DECLINING' | 'STABLE' | 'UNKNOWN';
  dataPoints: HistoricalDataPoint[];
}

// ─── Interventions ────────────────────────────────────────────────────────────

export interface InterventionCourse {
  rank: number;
  courseCode: string;
  courseName: string;
  faculty: string;
  failureRate: number;
  historicalDeviation: number | null;
  sectionDeviation: number | null;
  internalExternalGap: number | null;
  priorityScore: number;
  priorityLevel: PriorityLevel;
  reasons: string[];
}

export interface InterventionSummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

// ─── AI Narrative ─────────────────────────────────────────────────────────────

export interface AnalyticalNarrative {
  generatedAt?: string;
  model?: string;
  model_used?: string;
  summary: string;
  keyFindings: string[];
  key_findings?: string[];
  recommendations: string[];
  disclaimer: string;
}
