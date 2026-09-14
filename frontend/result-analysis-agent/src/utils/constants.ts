import type { ReportOption } from '@/types/report';

// ─── Academic constants ───────────────────────────────────────────────────────

export const ACADEMIC_YEARS = [
  '2026-27',
  '2025-26',
  '2024-25',
  '2023-24',
  '2022-23',
];

export const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8];

export const DEPARTMENTS = [
  'Computer Science & Engineering',
  'Electronics & Communication Engineering',
  'Mechanical Engineering',
  'Civil Engineering',
  'Electrical & Electronics Engineering',
  'Information Technology',
];

export const PROGRAMMES = ['B.Tech', 'M.Tech', 'MBA', 'MCA'];

export const BATCHES = ['2024', '2023', '2022', '2021', '2020'];

export const CURRENT_ACADEMIC_YEAR = '2025-26';
export const CURRENT_SEMESTER = 6;
export const CURRENT_DEPARTMENT = 'Computer Science & Engineering';

// ─── Grade scale ──────────────────────────────────────────────────────────────

export const GRADE_ORDER = ['A+', 'A', 'B+', 'B', 'C', 'D', 'F'];

export const GRADE_POINTS: Record<string, number> = {
  'A+': 10,
  A: 9,
  'B+': 8,
  B: 7,
  C: 6,
  D: 5,
  F: 0,
};

// ─── Priority thresholds ──────────────────────────────────────────────────────

export const PRIORITY_THRESHOLDS = {
  CRITICAL: 40,   // failure rate ≥ 40%
  HIGH: 25,       // failure rate ≥ 25%
  MEDIUM: 15,     // failure rate ≥ 15%
  LOW: 0,
};

// ─── Correlation thresholds ───────────────────────────────────────────────────

export const CORRELATION_THRESHOLDS = {
  STRONG_POSITIVE: 0.7,
  MODERATE_POSITIVE: 0.4,
  WEAK_POSITIVE: 0.1,
  WEAK_NEGATIVE: -0.1,
  STRONG_NEGATIVE: -0.7,
  MIN_DATA_POINTS: 5,
};

// ─── Upload constants ─────────────────────────────────────────────────────────

export const ACCEPTED_FILE_TYPES = ['.xlsx', '.xls', '.csv', '.pdf'];
export const MAX_FILE_SIZE_MB = 50;
export const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

// ─── Table defaults ───────────────────────────────────────────────────────────

export const DEFAULT_PAGE_SIZE = 20;
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// ─── Report options ───────────────────────────────────────────────────────────

export const REPORT_OPTIONS: ReportOption[] = [
  {
    type: 'SEMESTER_SUMMARY',
    label: 'Semester Summary Report',
    description: 'Complete semester result overview with all metrics, grade distribution, and executive summary.',
    icon: 'FileText',
    requiresCourse: false,
    requiresDepartment: false,
  },
  {
    type: 'DEPARTMENT',
    label: 'Department Report',
    description: 'Department-level analysis including course-wise performance and faculty metrics.',
    icon: 'Building2',
    requiresCourse: false,
    requiresDepartment: true,
  },
  {
    type: 'COURSE',
    label: 'Course Report',
    description: 'Detailed course analysis with section comparison, marks distribution, and historical comparison.',
    icon: 'BookOpen',
    requiresCourse: true,
    requiresDepartment: false,
  },
  {
    type: 'MERIT_LIST',
    label: 'Merit List',
    description: 'Programme and section toppers with ranks, GPA, and performance classification.',
    icon: 'Trophy',
    requiresCourse: false,
    requiresDepartment: false,
  },
  {
    type: 'INTERVENTION',
    label: 'Intervention Priority Report',
    description: 'Courses requiring attention ranked by priority score with detailed reasoning.',
    icon: 'AlertTriangle',
    requiresCourse: false,
    requiresDepartment: false,
  },
  {
    type: 'CORRELATION',
    label: 'Internal vs External Correlation Report',
    description: 'Statistical correlation analysis between internal assessment and external examination marks.',
    icon: 'TrendingUp',
    requiresCourse: false,
    requiresDepartment: false,
  },
];

// ─── Navigation items ─────────────────────────────────────────────────────────

export const NAV_ITEMS = [
  { path: '/dashboard',       label: 'Overview',             icon: 'LayoutDashboard' },
  { path: '/upload',          label: 'Upload Results',        icon: 'Upload' },
  { path: '/import-history',  label: 'Import History',        icon: 'History' },
  { path: '/courses',         label: 'Course Analysis',       icon: 'BookOpen' },
  { path: '/sections',        label: 'Section Analysis',      icon: 'Layers' },
  { path: '/faculty',         label: 'Faculty Analysis',      icon: 'Users' },
  { path: '/merit-list',      label: 'Merit List',            icon: 'Trophy' },
  { path: '/correlation',     label: 'Internal vs External',  icon: 'TrendingUp' },
  { path: '/historical',      label: 'Historical Trends',     icon: 'LineChart' },
  { path: '/interventions',   label: 'Interventions',         icon: 'AlertTriangle' },
  { path: '/ai-insights',     label: 'AI Insights',           icon: 'Sparkles' },
  { path: '/reports',         label: 'Reports',               icon: 'FileText' },
  { path: '/users',           label: 'User Management',       icon: 'UserCheck' },
  { path: '/settings',        label: 'Settings',              icon: 'Settings' },
] as const;

// ─── Roles ────────────────────────────────────────────────────────────────────

export const ROLES = {
  PLATFORM_ADMIN: 'PLATFORM_ADMIN',
  HOD: 'HOD',
  DEAN: 'DEAN',
  FACULTY: 'FACULTY',
  IQAC: 'IQAC',
  MANAGEMENT: 'MANAGEMENT',
} as const;

export type UserRole = keyof typeof ROLES;

// ─── Role-based navigation visibility ────────────────────────────────────────
// Paths hidden for each role (not visible = not rendered, not just disabled)

const HIDDEN_PATHS_BY_ROLE: Record<string, string[]> = {
  PLATFORM_ADMIN: [],  // sees everything
  DEAN: ['/upload', '/users', '/settings', '/audit-logs'],
  HOD: ['/upload', '/users', '/settings', '/audit-logs'],
  FACULTY: ['/upload', '/import-history', '/faculty', '/users', '/settings', '/audit-logs'],
  IQAC: ['/upload', '/users', '/settings', '/audit-logs'],
  MANAGEMENT: ['/upload', '/users', '/settings', '/audit-logs'],
  AUDITOR: ['/upload', '/users', '/settings'],
};

export function getVisibleNavItems(role?: string): typeof NAV_ITEMS[number][] {
  if (!role) return [];
  const hidden = HIDDEN_PATHS_BY_ROLE[role] ?? [];
  return NAV_ITEMS.filter((item) => !hidden.includes(item.path)) as typeof NAV_ITEMS[number][];
}
