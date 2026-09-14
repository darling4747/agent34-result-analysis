import { useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell, Legend,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { ChartCard } from '@/components/common/ChartCard';
import { DataTable, type Column } from '@/components/common/DataTable';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { StatCard } from '@/components/common/StatCard';
import { TableSkeleton } from '@/components/common/LoadingSkeleton';
import { useSections } from '@/hooks/useAnalysis';
import type { SectionMetrics } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import { formatGpa, formatMarks, formatPercentage } from '@/utils/formatters';
import { CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER } from '@/utils/constants';

const DEFAULT_FILTERS: ResultFilters = {
  academicYear: CURRENT_ACADEMIC_YEAR,
  semester: CURRENT_SEMESTER,
  department: CURRENT_DEPARTMENT,
};

const SECTION_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4'];

const COLUMNS: Column<SectionMetrics>[] = [
  { key: 'section',   header: 'Section',     accessor: (r) => <span className="font-semibold text-gray-900">Section {r.section}</span>,                                                                            sortValue: (r) => r.section },
  { key: 'programme', header: 'Programme',   accessor: (r) => <span className="text-xs">{r.programme} · {r.branch}</span> },
  { key: 'students',  header: 'Students',    accessor: (r) => r.studentCount,                                                                                                                                      sortValue: (r) => r.studentCount },
  { key: 'pass',      header: 'Pass Rate',   accessor: (r) => <span className={`font-medium ${r.passRate >= 80 ? 'text-emerald-700' : r.passRate >= 65 ? 'text-yellow-700' : 'text-red-700'}`}>{formatPercentage(r.passRate)}</span>, sortValue: (r) => r.passRate },
  { key: 'fail',      header: 'Failure Rate',accessor: (r) => formatPercentage(r.failureRate),                                                                                                                     sortValue: (r) => r.failureRate },
  { key: 'avg',       header: 'Avg Marks',   accessor: (r) => formatMarks(r.averageMarks),                                                                                                                         sortValue: (r) => r.averageMarks },
  { key: 'gpa',       header: 'Avg GPA',     accessor: (r) => formatGpa(r.averageGpa),                                                                                                                             sortValue: (r) => r.averageGpa },
  { key: 'top',       header: 'Top Score',   accessor: (r) => r.topScore != null ? formatMarks(r.topScore) : '—',                                                                                                  sortValue: (r) => r.topScore ?? 0 },
];

export default function SectionAnalysis() {
  const [filters, setFilters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const { data, loading, error, isNetworkError, retry } = useSections(filters);

  const best  = data ? [...data].sort((a, b) => b.passRate - a.passRate)[0] : null;
  const worst = data ? [...data].sort((a, b) => a.passRate - b.passRate)[0] : null;
  const gap   = best && worst ? best.passRate - worst.passRate : null;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Section Analysis"
        description="Compare academic performance across sections. Differences should be interpreted in context of cohort entry ability and course mix."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Section Analysis' }]}
      />

      <FilterBar
        filters={filters}
        onChange={(u) => setFilters((f) => ({ ...f, ...u }))}
        show={{ academicYear: true, semester: true, department: true, programme: true, course: true }}
      />

      {/* Context note */}
      <div className="bg-blue-50 border border-blue-200 rounded-md px-4 py-3 text-xs text-blue-800">
        Section comparisons reflect aggregate performance across all courses for the selected filters.
        Differences between sections should be assessed alongside cohort entry characteristics and
        course allocation before drawing conclusions.
      </div>

      {/* KPI strip */}
      {!loading && data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard title="Sections" value={data.length} accent="blue" />
          <StatCard title="Best Pass Rate" value={best ? formatPercentage(best.passRate) : '—'} subtitle={best ? `Section ${best.section}` : ''} accent="green" />
          <StatCard title="Lowest Pass Rate" value={worst ? formatPercentage(worst.passRate) : '—'} subtitle={worst ? `Section ${worst.section}` : ''} accent={worst && worst.passRate < 70 ? 'red' : 'orange'} />
          <StatCard title="Section Gap" value={gap != null ? formatPercentage(gap) : '—'} subtitle="between best and lowest" accent={gap != null && gap > 15 ? 'red' : 'gray'} />
        </div>
      )}

      {/* Comparison charts */}
      {!loading && data && data.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <ChartCard title="Pass Rate by Section" minHeight={200}>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="section" tickFormatter={(v) => `Sec ${v}`} tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                <Tooltip formatter={(v: any) => [`${v.toFixed(1)}%`]} contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="passRate" name="Pass Rate %" radius={[3, 3, 0, 0]}>
                  {data.map((s, i) => (
                    <Cell key={s.section} fill={SECTION_COLORS[i % SECTION_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard title="Average Marks by Section" minHeight={200}>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={data} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="section" tickFormatter={(v) => `Sec ${v}`} tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: any) => [v.toFixed(1), 'Avg Marks']} contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="averageMarks" name="Avg Marks" radius={[3, 3, 0, 0]} fill="#8b5cf6" />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}

      {/* Pass vs Fail grouped */}
      {!loading && data && data.length > 0 && (
        <ChartCard title="Pass vs Fail Count by Section" minHeight={200}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data} margin={{ top: 4, right: 16, left: -8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="section" tickFormatter={(v) => `Sec ${v}`} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="passCount"  name="Pass"  fill="#10b981" radius={[3, 3, 0, 0]} stackId="a" />
              <Bar dataKey="failCount"  name="Fail"  fill="#ef4444" radius={[3, 3, 0, 0]} stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Table */}
      {error ? (
        <ErrorState message={error} isNetworkError={isNetworkError} onRetry={retry} />
      ) : loading ? (
        <TableSkeleton rows={4} cols={7} />
      ) : !data?.length ? (
        <EmptyState title="No section data found" description="No sections match the selected filters." />
      ) : (
        <DataTable
          columns={COLUMNS}
          data={data}
          rowKey={(r) => r.section}
          caption="Section analysis table"
          paginate={false}
        />
      )}
    </div>
  );
}
