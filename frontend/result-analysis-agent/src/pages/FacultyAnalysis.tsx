import { Info } from 'lucide-react';
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
import { TableSkeleton } from '@/components/common/LoadingSkeleton';
import { useFaculty } from '@/hooks/useAnalysis';
import type { FacultyMetrics } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import { formatDeviation, formatMarks, formatPercentage } from '@/utils/formatters';
import { CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER } from '@/utils/constants';

const DEFAULT_FILTERS: ResultFilters = {
  academicYear: CURRENT_ACADEMIC_YEAR,
  semester: CURRENT_SEMESTER,
  department: CURRENT_DEPARTMENT,
};

// ─── Faculty detail panel ─────────────────────────────────────────────────────

function FacultyDetailPanel({ faculty, onClose }: { faculty: FacultyMetrics; onClose: () => void }) {
  return (
    <aside
      className="fixed inset-y-0 right-0 z-40 w-full max-w-lg bg-white border-l border-gray-200 shadow-xl flex flex-col overflow-y-auto"
      aria-label={`Faculty detail: ${faculty.facultyName}`}
    >
      <div className="flex items-start justify-between px-5 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
        <div>
          <h2 className="text-base font-semibold text-gray-900">{faculty.facultyName}</h2>
          <div className="text-xs text-gray-500 mt-0.5">{faculty.department}</div>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-700 p-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" aria-label="Close">✕</button>
      </div>

      <div className="flex flex-col gap-4 px-5 py-4">
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-xs text-amber-800">
          <strong>Contextual note:</strong> {faculty.contextNote}
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          {[
            { label: 'Pass Rate',          value: formatPercentage(faculty.passRate) },
            { label: 'Historical Baseline', value: faculty.historicalBaseline != null ? formatPercentage(faculty.historicalBaseline) : '—' },
            { label: 'Deviation',          value: faculty.deviation != null ? formatDeviation(faculty.deviation) : '—' },
            { label: 'Avg Marks',          value: formatMarks(faculty.averageMarks) },
            { label: 'Total Students',     value: faculty.totalStudents },
            { label: 'Courses Handled',    value: faculty.coursesHandled.length },
          ].map((m) => (
            <div key={m.label} className="bg-gray-50 border border-gray-200 rounded-md px-3 py-2">
              <div className="text-xs text-gray-500">{m.label}</div>
              <div className="text-base font-semibold text-gray-900 mt-0.5">{m.value}</div>
            </div>
          ))}
        </div>

        <div>
          <div className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1.5">Courses Handled</div>
          <div className="flex flex-wrap gap-1.5">
            {faculty.coursesHandled.map((c) => (
              <span key={c} className="px-2 py-0.5 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800 font-mono">{c}</span>
            ))}
          </div>
        </div>

        {faculty.coursesRequiringReview.length > 0 && (
          <div>
            <div className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-1.5">Courses Requiring Review</div>
            <div className="flex flex-wrap gap-1.5">
              {faculty.coursesRequiringReview.map((c) => (
                <span key={c} className="px-2 py-0.5 bg-red-50 border border-red-200 rounded text-xs text-red-800 font-mono">{c}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

// ─── Columns ──────────────────────────────────────────────────────────────────

function buildColumns(onSelect: (f: FacultyMetrics) => void): Column<FacultyMetrics>[] {
  return [
    {
      key: 'name',
      header: 'Faculty',
      accessor: (r) => (
        <button onClick={() => onSelect(r)} className="text-left focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
          <div className="font-medium text-blue-700 hover:text-blue-900">{r.facultyName}</div>
          <div className="text-xs text-gray-500">{r.department}</div>
        </button>
      ),
      sortValue: (r) => r.facultyName,
    },
    {
      key: 'courses',
      header: 'Courses',
      accessor: (r) => {
        const list = Array.isArray(r.coursesHandled) ? r.coursesHandled : [];
        return <span className="text-xs font-mono text-gray-700">{list.join(', ') || '—'}</span>;
      },
    },
    { key: 'students',  header: 'Students',         accessor: (r) => r.totalStudents,                                                                                                                sortValue: (r) => r.totalStudents },
    { key: 'avg',       header: 'Avg Marks',        accessor: (r) => formatMarks(r.averageMarks),                                                                                                     sortValue: (r) => r.averageMarks },
    { key: 'pass',      header: 'Pass Rate',        accessor: (r) => <span className={`font-medium ${r.passRate >= 75 ? 'text-emerald-700' : r.passRate >= 60 ? 'text-yellow-700' : 'text-red-700'}`}>{formatPercentage(r.passRate)}</span>, sortValue: (r) => r.passRate },
    { key: 'baseline',  header: 'Hist. Baseline',   accessor: (r) => r.historicalBaseline != null ? formatPercentage(r.historicalBaseline) : <span className="text-gray-400 text-xs">—</span>,       sortValue: (r) => r.historicalBaseline ?? 0 },
    {
      key: 'dev',
      header: 'Deviation',
      accessor: (r) => r.deviation != null
        ? <span className={`text-xs font-medium ${r.deviation >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatDeviation(r.deviation)}</span>
        : <span className="text-gray-400 text-xs">—</span>,
      sortValue: (r) => r.deviation ?? 0,
    },
    {
      key: 'review',
      header: 'Review Needed',
      accessor: (r) => {
        const reviewList = Array.isArray(r.coursesRequiringReview) ? r.coursesRequiringReview : [];
        return reviewList.length > 0
          ? <span className="text-xs text-red-700 font-medium">{reviewList.join(', ')}</span>
          : <span className="text-emerald-600 text-xs">—</span>;
      },
    },
  ];
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FacultyAnalysis() {
  const [filters, setFilters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const [selected, setSelected] = useState<FacultyMetrics | null>(null);
  const { data, loading, error, isNetworkError, retry } = useFaculty(filters);

  const columns = buildColumns(setSelected);

  const chartData = data?.map((f) => ({
    name: f.facultyName.split(' ').pop() ?? f.facultyName,
    passRate: f.passRate,
    baseline: f.historicalBaseline ?? 0,
  })) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Faculty Analysis"
        description="Course-level metrics by faculty with contextual factors. Not a standalone faculty ranking."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Faculty Analysis' }]}
      />

      <FilterBar
        filters={filters}
        onChange={(u) => setFilters((f) => ({ ...f, ...u }))}
        show={{ academicYear: true, semester: true, department: true }}
      />

      {/* Important disclaimer */}
      <div className="flex items-start gap-2.5 bg-blue-50 border border-blue-200 rounded-md px-4 py-3" role="note">
        <Info size={15} className="text-blue-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <p className="text-xs text-blue-800">
          <strong>Contextual note:</strong> Faculty metrics are presented alongside course difficulty,
          section cohort characteristics, and historical pass rate baselines. These metrics should
          not be interpreted as standalone faculty performance rankings.
        </p>
      </div>

      {/* Pass rate vs baseline chart */}
      {!loading && chartData.length > 0 && (
        <ChartCard
          title="Pass Rate vs Historical Baseline"
          subtitle="Faculty grouped by course handled"
          minHeight={220}
        >
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} margin={{ top: 4, right: 16, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
              <Tooltip formatter={(v: any) => [`${Number(v).toFixed(1)}%`]} contentStyle={{ fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="passRate" name="Current Pass Rate" fill="#3b82f6" radius={[3, 3, 0, 0]}>
                {chartData.map((d, i) => (
                  <Cell key={i} fill={d.passRate >= (d.baseline || 0) ? '#10b981' : '#ef4444'} />
                ))}
              </Bar>
              <Bar dataKey="baseline" name="Historical Baseline" fill="#d1d5db" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Table */}
      {error ? (
        <ErrorState message={error} isNetworkError={isNetworkError} onRetry={retry} />
      ) : loading ? (
        <TableSkeleton rows={5} cols={8} />
      ) : !data?.length ? (
        <EmptyState title="No faculty data found" description="No faculty metrics are available for the selected filters." />
      ) : (
        <DataTable
          columns={columns}
          data={data}
          rowKey={(r) => r.facultyId}
          searchable
          searchPlaceholder="Search by faculty name or course…"
          searchFilter={(r, q) =>
            r.facultyName.toLowerCase().includes(q) ||
            r.coursesHandled.some((c) => c.toLowerCase().includes(q))
          }
          caption="Faculty analysis table"
        />
      )}

      {selected && (
        <>
          <div className="fixed inset-0 z-30 bg-black/20" onClick={() => setSelected(null)} aria-hidden="true" />
          <FacultyDetailPanel faculty={selected} onClose={() => setSelected(null)} />
        </>
      )}
    </div>
  );
}
