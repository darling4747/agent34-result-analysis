import type {
  AnalyticalNarrative,
  CorrelationResult,
  CourseDetail,
  CourseMetrics,
  FacultyMetrics,
  GradeDistributionItem,
  HistoricalComparison,
  InterventionCourse,
  InterventionSummary,
  MeritEntry,
  ResultSummary,
  SectionMetrics,
} from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import apiClient from './client';

// ─── Helpers ──────────────────────────────────────────────────────────────────

function toParams(filters: ResultFilters): Record<string, string> {
  const params: Record<string, string> = {};
  if (filters.academicYear)  params['academic_year'] = filters.academicYear;
  if (filters.semester != null) params['semester'] = String(filters.semester);
  if (filters.department)    params['department']   = filters.department;
  if (filters.programme)     params['programme']    = filters.programme;
  if (filters.batch)         params['batch']        = filters.batch;
  if (filters.section)       params['section']      = filters.section;
  if (filters.courseCode)    params['course_code']  = filters.courseCode;
  return params;
}

function unwrap<T>(data: any): T {
  if (data && typeof data === 'object' && 'data' in data) {
    return data.data;
  }
  return data;
}

// ─── Summary ──────────────────────────────────────────────────────────────────

/** GET /api/analysis/summary */
export async function getSummary(filters: ResultFilters): Promise<ResultSummary> {
  const response = await apiClient.get<any>('/api/analysis/summary', {
    params: toParams(filters),
  });
  const raw = unwrap<any>(response.data) ?? {};
  return {
    totalStudents: raw.totalStudents ?? raw.total_students ?? 0,
    totalResults: raw.totalResults ?? raw.total_results ?? 0,
    passCount: raw.passCount ?? raw.pass_count ?? 0,
    failCount: raw.failCount ?? raw.fail_count ?? 0,
    passPercentage: raw.passPercentage ?? raw.pass_percentage ?? 0,
    failPercentage: raw.failPercentage ?? raw.failure_percentage ?? raw.fail_percentage ?? 0,
    averageMarks: raw.averageMarks ?? raw.average_marks ?? 0,
    averageGpa: raw.averageGpa ?? raw.average_gpa ?? 0,
    previousPassPercentage: raw.previousPassPercentage ?? raw.previous_pass_percentage ?? null,
    previousAverageMarks: raw.previousAverageMarks ?? raw.previous_average_marks ?? null,
    semester: raw.semester ?? 0,
    academicYear: raw.academicYear ?? raw.academic_year ?? '',
    department: raw.department ?? '',
  };
}

// ─── Grade Distribution ───────────────────────────────────────────────────────

/** GET /api/analysis/grades */
export async function getGradeDistribution(filters: ResultFilters): Promise<GradeDistributionItem[]> {
  const response = await apiClient.get<any>('/api/analysis/grades', {
    params: toParams(filters),
  });
  return unwrap<GradeDistributionItem[]>(response.data) ?? [];
}

// ─── Courses ──────────────────────────────────────────────────────────────────

/** GET /api/analysis/courses */
export async function getCourses(filters: ResultFilters): Promise<CourseMetrics[]> {
  const response = await apiClient.get<any>('/api/analysis/courses', {
    params: toParams(filters),
  });
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map((c) => ({
    courseCode: c.courseCode ?? c.course_code ?? '',
    courseName: c.courseName ?? c.course_name ?? '',
    faculty: c.faculty ?? c.faculty_name ?? '',
    credits: c.credits ?? 0,
    studentCount: c.studentCount ?? c.total_students ?? 0,
    passCount: c.passCount ?? c.pass_count ?? 0,
    failCount: c.failCount ?? c.fail_count ?? 0,
    passPercentage: c.passPercentage ?? c.pass_percentage ?? 0,
    failurePercentage: c.failurePercentage ?? c.failure_percentage ?? 0,
    averageMarks: c.averageMarks ?? c.average_marks ?? 0,
    averageGpa: c.averageGpa ?? c.average_gpa ?? 0,
    historicalDeviation: c.historicalDeviation ?? c.historical_deviation ?? null,
    priorityLevel: c.priorityLevel ?? c.priority_level ?? 'LOW',
    gradeDistribution: c.gradeDistribution ?? c.grade_distribution ?? [],
  }));
}

/** GET /api/analysis/courses/:courseCode */
export async function getCourseDetail(
  courseCode: string,
  filters: ResultFilters,
): Promise<CourseDetail> {
  const response = await apiClient.get<any>(`/api/analysis/courses/${courseCode}`, {
    params: toParams(filters),
  });
  return unwrap<CourseDetail>(response.data);
}

// ─── Sections ─────────────────────────────────────────────────────────────────

/** GET /api/analysis/sections */
export async function getSections(filters: ResultFilters): Promise<SectionMetrics[]> {
  const response = await apiClient.get<any>('/api/analysis/sections', {
    params: toParams(filters),
  });
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map((s) => ({
    section: String(s.section ?? ''),
    programme: s.programme ?? '',
    branch: s.branch ?? s.department ?? '',
    studentCount: s.studentCount ?? s.student_count ?? s.total_students ?? 0,
    passCount: s.passCount ?? s.pass_count ?? 0,
    failCount: s.failCount ?? s.fail_count ?? 0,
    passRate: s.passRate ?? s.pass_rate ?? s.pass_percentage ?? 0,
    failureRate: s.failureRate ?? s.failure_rate ?? s.failure_percentage ?? 0,
    averageMarks: s.averageMarks ?? s.average_marks ?? s.avg_marks ?? 0,
    averageGpa: s.averageGpa ?? s.average_gpa ?? s.avg_gpa ?? 0,
    topScore: s.topScore ?? s.top_score ?? null,
    lowestScore: s.lowestScore ?? s.lowest_score ?? null,
  }));
}

// ─── Faculty ──────────────────────────────────────────────────────────────────

/** GET /api/analysis/faculty */
export async function getFaculty(filters: ResultFilters): Promise<FacultyMetrics[]> {
  const response = await apiClient.get<any>('/api/analysis/faculty', {
    params: toParams(filters),
  });
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map((f) => {
    const rawCourses = f.coursesHandled ?? f.courses_handled;
    const coursesHandled = Array.isArray(rawCourses)
      ? rawCourses.map(String)
      : typeof rawCourses === 'string' && rawCourses
      ? [rawCourses]
      : [];

    const rawReview = f.coursesRequiringReview ?? f.courses_requiring_review;
    const coursesRequiringReview = Array.isArray(rawReview)
      ? rawReview.map(String)
      : typeof rawReview === 'string' && rawReview
      ? [rawReview]
      : [];

    return {
      facultyId: f.facultyId ?? f.employee_id ?? String(f.id ?? ''),
      facultyName: f.facultyName ?? f.faculty_name ?? '',
      department: f.department ?? '',
      coursesHandled,
      totalStudents: f.totalStudents ?? f.total_students ?? 0,
      averageMarks: f.averageMarks ?? f.average_marks ?? 0,
      passRate: f.passRate ?? f.pass_rate ?? f.pass_percentage ?? 0,
      historicalBaseline: f.historicalBaseline ?? f.historical_baseline ?? null,
      deviation: f.deviation ?? null,
      coursesRequiringReview,
      contextNote: f.contextNote ?? f.context_note ?? '',
    };
  });
}

// ─── Merit List ───────────────────────────────────────────────────────────────

/** GET /api/analysis/merit-list */
export async function getMeritList(filters: ResultFilters): Promise<MeritEntry[]> {
  const response = await apiClient.get<any>('/api/analysis/merit-list', {
    params: toParams(filters),
  });
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map((m) => ({
    rank: m.rank ?? 0,
    rollNumber: m.rollNumber ?? m.roll_number ?? '',
    studentName: m.studentName ?? m.student_name ?? '',
    programme: m.programme ?? '',
    branch: m.branch ?? m.department ?? '',
    section: m.section ?? '',
    batch: m.batch ?? '',
    sgpa: m.sgpa ?? 0,
    cgpa: m.cgpa ?? null,
    totalMarks: m.totalMarks ?? m.total_marks ?? 0,
    status: m.status ?? 'PASS',
    scope: m.scope ?? 'PROGRAMME',
  }));
}

// ─── Correlation ──────────────────────────────────────────────────────────────

/** GET /api/analysis/correlation */
export async function getCorrelation(filters: ResultFilters): Promise<CorrelationResult[]> {
  const response = await apiClient.get<any>('/api/analysis/correlation', {
    params: toParams(filters),
  });
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map((c) => ({
    courseCode: c.courseCode ?? c.course_code ?? '',
    courseName: c.courseName ?? c.course_name ?? '',
    studentCount: c.studentCount ?? c.student_count ?? 0,
    internalAverage: c.internalAverage ?? c.internal_average ?? 0,
    externalAverage: c.externalAverage ?? c.external_average ?? 0,
    pearsonCorrelation: c.pearsonCorrelation ?? c.pearson_correlation ?? null,
    interpretation: c.interpretation ?? 'INSUFFICIENT_DATA',
    flags: c.flags ?? [],
    scatterData: (c.scatterData ?? c.scatter_data ?? []).map((s: any) => ({
      rollNumber: s.rollNumber ?? s.roll_number ?? '',
      internalMarks: s.internalMarks ?? s.internal_marks ?? 0,
      externalMarks: s.externalMarks ?? s.external_marks ?? 0,
    })),
  }));
}

// ─── Historical ───────────────────────────────────────────────────────────────

/** GET /api/analysis/historical */
export async function getHistorical(filters: ResultFilters): Promise<HistoricalComparison[]> {
  const response = await apiClient.get<any>('/api/analysis/historical', {
    params: toParams(filters),
  });
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map((h) => ({
    courseCode: h.courseCode ?? h.course_code ?? '',
    courseName: h.courseName ?? h.course_name ?? '',
    currentValue: h.currentValue ?? h.current_value ?? 0,
    previousValue: h.previousValue ?? h.previous_value ?? null,
    historicalAverage: h.historicalAverage ?? h.historical_average ?? null,
    deviationFromAverage: h.deviationFromAverage ?? h.deviation_from_average ?? null,
    trend: h.trend ?? 'UNKNOWN',
    dataPoints: (h.dataPoints ?? h.data_points ?? []).map((dp: any) => ({
      academicYear: dp.academicYear ?? dp.academic_year ?? '',
      semester: dp.semester ?? 0,
      label: dp.label ?? '',
      passRate: dp.passRate ?? dp.pass_rate ?? 0,
      averageMarks: dp.averageMarks ?? dp.average_marks ?? 0,
      averageGpa: dp.averageGpa ?? dp.average_gpa ?? 0,
      failureRate: dp.failureRate ?? dp.failure_rate ?? 0,
      studentCount: dp.studentCount ?? dp.student_count ?? 0,
    })),
  }));
}

// ─── Interventions ────────────────────────────────────────────────────────────

/** GET /api/analysis/interventions */
export async function getInterventions(filters: ResultFilters): Promise<InterventionCourse[]> {
  const response = await apiClient.get<any>('/api/analysis/interventions', {
    params: toParams(filters),
  });
  const list = unwrap<any[]>(response.data) ?? [];
  return list.map((i) => ({
    rank: i.rank ?? 0,
    courseCode: i.courseCode ?? i.course_code ?? '',
    courseName: i.courseName ?? i.course_name ?? '',
    faculty: i.faculty ?? i.faculty_name ?? '',
    failureRate: i.failureRate ?? i.failure_rate ?? 0,
    historicalDeviation: i.historicalDeviation ?? i.historical_deviation ?? null,
    sectionDeviation: i.sectionDeviation ?? i.section_deviation ?? null,
    internalExternalGap: i.internalExternalGap ?? i.internal_external_gap ?? null,
    priorityScore: i.priorityScore ?? i.priority_score ?? 0,
    priorityLevel: i.priorityLevel ?? i.priority_level ?? 'LOW',
    reasons: i.reasons ?? [],
  }));
}

/** GET /api/analysis/interventions/summary */
export async function getInterventionSummary(filters: ResultFilters): Promise<InterventionSummary> {
  const response = await apiClient.get<any>('/api/analysis/interventions/summary', {
    params: toParams(filters),
  });
  return unwrap<InterventionSummary>(response.data) ?? { critical: 0, high: 0, medium: 0, low: 0, total: 0 };
}

// ─── Narrative ────────────────────────────────────────────────────────────────

/** GET /api/analysis/narrative */
export async function getNarrative(filters: ResultFilters): Promise<AnalyticalNarrative> {
  const response = await apiClient.get<any>('/api/analysis/narrative', {
    params: toParams(filters),
  });
  const raw = unwrap<any>(response.data) ?? {};
  return {
    generatedAt: raw.generatedAt ?? raw.generated_at ?? new Date().toISOString(),
    model: raw.model ?? raw.model_used ?? 'deterministic',
    model_used: raw.model_used ?? raw.model,
    summary: raw.summary ?? '',
    keyFindings: raw.keyFindings ?? raw.key_findings ?? [],
    key_findings: raw.key_findings ?? raw.keyFindings ?? [],
    recommendations: raw.recommendations ?? [],
    disclaimer: raw.disclaimer ?? '',
  };
}

/** POST /api/analysis/narrative/generate
 * Auto-collects active dataset metrics, sends to Gemini, returns narrative.
 */
export async function generateAutoNarrative(
  filters: ResultFilters = {},
): Promise<{ success: boolean; data: import('@/types/analysis').AnalyticalNarrative }> {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v != null)
  );
  const response = await apiClient.post('/api/analysis/narrative/generate', {}, { params });
  return response.data;
}
