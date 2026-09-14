import { useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts';
import { ChartCard } from '@/components/common/ChartCard';
import { DataTable, type Column } from '@/components/common/DataTable';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { PriorityBadge } from '@/components/common/PriorityBadge';
import { StatCard } from '@/components/common/StatCard';
import { TableSkeleton } from '@/components/common/LoadingSkeleton';
import { useCourses } from '@/hooks/useAnalysis';
import type { CourseMetrics } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import {
  CHART_COLORS, GRADE_COLORS,
  formatDeviation, formatGpa, formatMarks, formatPercentage,
} from '@/utils/formatters';
import {
  CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER,
} from '@/utils/constants';

const DEFAULT_FILTERS: ResultFilters = {
  academicYear: CURRENT_ACADEMIC_YEAR,
  semester: CURRENT_SEMESTER,
  department: CURRENT_DEPARTMENT,
};

// ─── Course detail drawer ─────────────────────────────────────────────────────

function CourseDetailPanel({ course, onClose }: { course: CourseMetrics; onClose: () => void }) {
  return (
    <aside
      className="fixed inset-y-0 right-0 z-40 w-full max-w-lg bg-white border-l border-gray-200 shadow-xl flex flex-col overflow-y-auto"
      aria-label={`Detail: ${course.courseName}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between px-5 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
        <div>
          <div className="text-xs text-gray-500 font-mono">{course.courseCode}</div>
          <h2 className="text-base font-semibold text-gray-900 mt-0.5">{course.courseName}</h2>
          <div className="text-xs text-gray-500 mt-0.5">{course.faculty} · {course.credits} credits</div>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-700 p-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="Close detail panel"
        >
          ✕
        </button>
      </div>

      <div className="flex flex-col gap-5 px-5 py-4">
        {/* KPIs */}
        <div className="grid grid-cols-2 gap-3">
          <StatCard title="Pass %" value={formatPercentage(course.passPercentage)} accent={course.passPercentage >= 75 ? 'green' : 'red'} />
          <StatCard title="Failure %" value={formatPercentage(course.failurePercentage)} accent={course.failurePercentage > 25 ? 'red' : 'orange'} />
          <StatCard title="Avg Marks" value={formatMarks(course.averageMarks)} accent="blue" />
          <StatCard title="Avg GPA" value={formatGpa(course.averageGpa)} accent="purple" />
        </div>

        {/* Grade distribution */}
        <ChartCard title="Grade Distribution" minHeight={200}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={course.gradeDistribution} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="grade" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip formatter={(v: any) => [v, 'Students']} contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" radius={[3, 3, 0, 0]} name="Students">
                {course.gradeDistribution.map((g) => (
                  <Cell key={g.grade} fill={GRADE_COLORS[g.grade] ?? CHART_COLORS[0]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Historical deviation */}
        <div className="bg-gray-50 rounded-md border border-gray-200 px-4 py-3">
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">Historical Comparison</div>
          <div className="flex items-center gap-4">
            <div>
              <div className="text-xs text-gray-500">Pass Rate (current)</div>
              <div className="text-lg font-semibold text-gray-900">{formatPercentage(course.passPercentage)}</div>
            </div>
            {course.historicalDeviation != null && (
              <div>
                <div className="text-xs text-gray-500">vs Historical Avg</div>
                <div className={`text-lg font-semibold ${course.historicalDeviation >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
                  {formatDeviation(course.historicalDeviation)}
                </div>
              </div>
            )}
          </div>
          {course.historicalDeviation != null && course.historicalDeviation < -5 && (
            <div className="mt-2 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-1.5">
              Significant decline from historical average. Review recommended.
            </div>
          )}
        </div>

        {/* Priority */}
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">Intervention Priority:</span>
          <PriorityBadge level={course.priorityLevel} size="md" />
        </div>
      </div>
    </aside>
  );
}

// ─── Columns ──────────────────────────────────────────────────────────────────

function buildColumns(onSelect: (c: CourseMetrics) => void): Column<CourseMetrics>[] {
  return [
    {
      key: 'code',
      header: 'Course',
      accessor: (r) => (
        <button
          onClick={() => onSelect(r)}
          className="text-left focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
        >
          <div className="font-medium text-blue-700 hover:text-blue-900">{r.courseCode}</div>
          <div className="text-xs text-gray-500 max-w-[200px] truncate">{r.courseName}</div>
        </button>
      ),
      sortValue: (r) => r.courseCode,
    },
    { key: 'faculty',   header: 'Faculty',    accessor: (r) => <span className="text-xs text-gray-600">{r.faculty}</span>,                                          sortValue: (r) => r.faculty },
    { key: 'students',  header: 'Students',   accessor: (r) => r.studentCount,                                                                                       sortValue: (r) => r.studentCount },
    { key: 'pass',      header: 'Pass %',     accessor: (r) => <span className={`font-medium ${r.passPercentage >= 75 ? 'text-emerald-700' : r.passPercentage >= 60 ? 'text-yellow-700' : 'text-red-700'}`}>{formatPercentage(r.passPercentage)}</span>,  sortValue: (r) => r.passPercentage },
    { key: 'fail',      header: 'Failure %',  accessor: (r) => formatPercentage(r.failurePercentage),                                                                sortValue: (r) => r.failurePercentage },
    { key: 'avg',       header: 'Avg Marks',  accessor: (r) => formatMarks(r.averageMarks),                                                                          sortValue: (r) => r.averageMarks },
    { key: 'gpa',       header: 'Avg GPA',    accessor: (r) => formatGpa(r.averageGpa),                                                                              sortValue: (r) => r.averageGpa },
    {
      key: 'dev',
      header: 'Hist. Δ',
      accessor: (r) => r.historicalDeviation != null
        ? <span className={`text-xs font-medium ${r.historicalDeviation >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatDeviation(r.historicalDeviation)}</span>
        : <span className="text-gray-400 text-xs">—</span>,
      sortValue: (r) => r.historicalDeviation ?? -999,
    },
    { key: 'priority',  header: 'Priority',   accessor: (r) => <PriorityBadge level={r.priorityLevel} /> },
  ];
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function CourseAnalysis() {
  const [filters, setFilters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const [selected, setSelected] = useState<CourseMetrics | null>(null);
  const { data, loading, error, isNetworkError, retry } = useCourses(filters);

  const columns = buildColumns(setSelected);

  const avgPass    = data ? data.reduce((s, c) => s + c.passPercentage, 0) / data.length : 0;
  const critical   = data?.filter((c) => c.priorityLevel === 'CRITICAL').length ?? 0;
  const highRisk   = data?.filter((c) => c.priorityLevel === 'HIGH').length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Course Analysis"
        description="Performance metrics for each course. Click a course for detailed breakdown."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Course Analysis' }]}
      />

      <FilterBar
        filters={filters}
        onChange={(u) => setFilters((f) => ({ ...f, ...u }))}
        show={{ academicYear: true, semester: true, department: true, programme: true }}
      />

      {/* Summary strip */}
      {!loading && data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard title="Courses" value={data.length} accent="blue" />
          <StatCard title="Dept Avg Pass %" value={formatPercentage(avgPass)} accent={avgPass >= 75 ? 'green' : 'red'} />
          <StatCard title="Critical" value={critical} subtitle="courses flagged" accent={critical > 0 ? 'red' : 'green'} />
          <StatCard title="High Priority" value={highRisk} subtitle="courses flagged" accent={highRisk > 0 ? 'orange' : 'green'} />
        </div>
      )}

      {/* Chart summary */}
      {!loading && data && (
        <ChartCard title="Pass % by Course" subtitle="Sorted by pass rate">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart
              data={[...data].sort((a, b) => a.passPercentage - b.passPercentage)}
              layout="vertical"
              margin={{ top: 4, right: 16, left: 80, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
              <YAxis type="category" dataKey="courseCode" tick={{ fontSize: 11 }} width={72} />
              <Tooltip formatter={(v: any) => [`${Number(v).toFixed(1)}%`, 'Pass Rate']} contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="passPercentage" name="Pass %" radius={[0, 3, 3, 0]}>
                {[...data].sort((a, b) => a.passPercentage - b.passPercentage).map((c) => (
                  <Cell
                    key={c.courseCode}
                    fill={c.passPercentage >= 75 ? '#10b981' : c.passPercentage >= 60 ? '#f59e0b' : '#ef4444'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Table */}
      {error ? (
        <ErrorState message={error} isNetworkError={isNetworkError} onRetry={retry} />
      ) : loading ? (
        <TableSkeleton rows={7} cols={8} />
      ) : !data?.length ? (
        <EmptyState title="No courses found" description="No course data is available for the selected filters." />
      ) : (
        <DataTable
          columns={columns}
          data={data}
          rowKey={(r) => r.courseCode}
          searchable
          searchPlaceholder="Search by course code or name…"
          searchFilter={(r, q) =>
            r.courseCode.toLowerCase().includes(q) ||
            r.courseName.toLowerCase().includes(q) ||
            r.faculty.toLowerCase().includes(q)
          }
          caption="Course analysis table"
        />
      )}

      {/* Detail drawer */}
      {selected && (
        <>
          <div className="fixed inset-0 z-30 bg-black/20" onClick={() => setSelected(null)} aria-hidden="true" />
          <CourseDetailPanel course={selected} onClose={() => setSelected(null)} />
        </>
      )}
    </div>
  );
}
