import type { PriorityLevel } from '@/types/analysis';
import type { CorrelationInterpretation } from '@/types/analysis';

// ─── Number formatters ────────────────────────────────────────────────────────

export function formatPercentage(value: number | null | undefined, decimals = 1): string {
  if (value == null) return '—';
  return `${value.toFixed(decimals)}%`;
}

export function formatMarks(value: number | null | undefined, decimals = 1): string {
  if (value == null) return '—';
  return value.toFixed(decimals);
}

export function formatGpa(value: number | null | undefined): string {
  if (value == null) return '—';
  return value.toFixed(2);
}

export function formatCount(value: number | null | undefined): string {
  if (value == null) return '—';
  return value.toLocaleString('en-IN');
}

export function formatDeviation(value: number | null | undefined): string {
  if (value == null) return '—';
  const sign = value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

export function formatCorrelation(value: number | null | undefined): string {
  if (value == null) return '—';
  return value.toFixed(3);
}

// ─── Date / time formatters ───────────────────────────────────────────────────

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso));
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(iso));
}

// ─── Label helpers ────────────────────────────────────────────────────────────

export function priorityLabel(level: PriorityLevel): string {
  const labels: Record<PriorityLevel, string> = {
    CRITICAL: 'Critical',
    HIGH: 'High',
    MEDIUM: 'Medium',
    LOW: 'Low',
  };
  return labels[level] ?? level;
}

export function correlationLabel(interp: CorrelationInterpretation): string {
  const labels: Record<CorrelationInterpretation, string> = {
    STRONG_POSITIVE: 'Strong positive relationship',
    MODERATE_POSITIVE: 'Moderate positive relationship',
    WEAK_POSITIVE: 'Weak positive relationship',
    WEAK_NEGATIVE: 'Weak negative relationship',
    STRONG_NEGATIVE: 'Strong negative relationship',
    INSUFFICIENT_DATA: 'Insufficient data',
  };
  return labels[interp] ?? interp;
}

export function semesterLabel(semester: number): string {
  const ordinals = ['', '1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th'];
  return ordinals[semester] ? `${ordinals[semester]} Semester` : `Semester ${semester}`;
}

export function trendLabel(trend: string): string {
  const labels: Record<string, string> = {
    IMPROVING: 'Improving',
    DECLINING: 'Declining',
    STABLE: 'Stable',
    UNKNOWN: 'Unknown',
  };
  return labels[trend] ?? trend;
}

// ─── Colour helpers (Tailwind class strings) ──────────────────────────────────

export function priorityColorClass(level: PriorityLevel): string {
  const map: Record<PriorityLevel, string> = {
    CRITICAL: 'bg-red-100 text-red-800 border-red-200',
    HIGH: 'bg-orange-100 text-orange-800 border-orange-200',
    MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    LOW: 'bg-green-100 text-green-800 border-green-200',
  };
  return map[level] ?? 'bg-gray-100 text-gray-800 border-gray-200';
}

export function priorityDotClass(level: PriorityLevel): string {
  const map: Record<PriorityLevel, string> = {
    CRITICAL: 'bg-red-500',
    HIGH: 'bg-orange-500',
    MEDIUM: 'bg-yellow-500',
    LOW: 'bg-green-500',
  };
  return map[level] ?? 'bg-gray-400';
}

export function gradeColorClass(grade: string): string {
  const map: Record<string, string> = {
    'A+': 'text-emerald-700 font-semibold',
    A: 'text-green-700 font-semibold',
    'B+': 'text-blue-700',
    B: 'text-blue-600',
    C: 'text-yellow-700',
    D: 'text-orange-700',
    F: 'text-red-700 font-semibold',
  };
  return map[grade] ?? 'text-gray-700';
}

export function statusColorClass(status: string): string {
  const map: Record<string, string> = {
    PASS: 'bg-green-100 text-green-800 border-green-200',
    FAIL: 'bg-red-100 text-red-800 border-red-200',
    ABSENT: 'bg-gray-100 text-gray-700 border-gray-200',
    WITHHELD: 'bg-purple-100 text-purple-800 border-purple-200',
  };
  return map[status] ?? 'bg-gray-100 text-gray-700 border-gray-200';
}

export function trendColorClass(trend: string): string {
  const map: Record<string, string> = {
    IMPROVING: 'text-green-600',
    DECLINING: 'text-red-600',
    STABLE: 'text-blue-600',
    UNKNOWN: 'text-gray-500',
  };
  return map[trend] ?? 'text-gray-500';
}

// ─── Chart colour palette ─────────────────────────────────────────────────────

export const GRADE_COLORS: Record<string, string> = {
  'A+': '#059669',
  A: '#10b981',
  'B+': '#3b82f6',
  B: '#60a5fa',
  C: '#f59e0b',
  D: '#f97316',
  F: '#ef4444',
};

export const CHART_COLORS = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#06b6d4',
  '#f97316',
  '#6366f1',
];

export const PASS_FAIL_COLORS = {
  pass: '#10b981',
  fail: '#ef4444',
};
