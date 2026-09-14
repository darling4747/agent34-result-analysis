import { AlertTriangle, Info } from 'lucide-react';
import { useState } from 'react';
import {
  CartesianGrid, ResponsiveContainer, Scatter,
  ScatterChart, Tooltip, XAxis, YAxis, ZAxis,
  ReferenceLine,
} from 'recharts';
import { ChartCard } from '@/components/common/ChartCard';
import { DataTable, type Column } from '@/components/common/DataTable';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { StatCard } from '@/components/common/StatCard';
import { TableSkeleton } from '@/components/common/LoadingSkeleton';
import { useCorrelation } from '@/hooks/useAnalysis';
import type { CorrelationResult } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import { correlationLabel, formatCorrelation, formatMarks } from '@/utils/formatters';
import { CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER } from '@/utils/constants';

const DEFAULT_FILTERS: ResultFilters = {
  academicYear: CURRENT_ACADEMIC_YEAR,
  semester: CURRENT_SEMESTER,
  department: CURRENT_DEPARTMENT,
};

// ─── Correlation colour ───────────────────────────────────────────────────────

function correlationColor(r: number | null): string {
  if (r == null) return 'text-gray-400';
  if (r >= 0.7) return 'text-emerald-700';
  if (r >= 0.4) return 'text-blue-700';
  if (r >= 0.1) return 'text-yellow-700';
  if (r >= -0.1) return 'text-orange-700';
  return 'text-red-700';
}

// ─── Flag badge ───────────────────────────────────────────────────────────────

const FLAG_LABELS: Record<string, string> = {
  HIGH_INTERNAL_LOW_EXTERNAL:  'High internal / low external',
  LARGE_INTERNAL_EXTERNAL_GAP: 'Large I/E gap',
  WEAK_CORRELATION:            'Weak correlation',
  NEGATIVE_CORRELATION:        'Negative correlation',
};

// ─── Summary table columns ────────────────────────────────────────────────────

function buildColumns(onSelect: (c: CorrelationResult) => void): Column<CorrelationResult>[] {
  return [
    {
      key: 'course',
      header: 'Course',
      accessor: (r) => (
        <button onClick={() => onSelect(r)} className="text-left focus:outline-none focus:ring-2 focus:ring-blue-500 rounded">
          <div className="font-medium text-blue-700 hover:text-blue-900">{r.courseCode}</div>
          <div className="text-xs text-gray-500">{r.courseName}</div>
        </button>
      ),
      sortValue: (r) => r.courseCode,
    },
    { key: 'n',       header: 'Students',    accessor: (r) => r.studentCount,                                                                                                    sortValue: (r) => r.studentCount },
    { key: 'intAvg',  header: 'Internal Avg', accessor: (r) => formatMarks(r.internalAverage),                                                                                   sortValue: (r) => r.internalAverage },
    { key: 'extAvg',  header: 'External Avg', accessor: (r) => formatMarks(r.externalAverage),                                                                                   sortValue: (r) => r.externalAverage },
    {
      key: 'r',
      header: 'Pearson r',
      accessor: (row) => (
        <span className={`font-semibold font-mono ${correlationColor(row.pearsonCorrelation)}`}>
          {formatCorrelation(row.pearsonCorrelation)}
        </span>
      ),
      sortValue: (r) => r.pearsonCorrelation ?? -2,
    },
    {
      key: 'interp',
      header: 'Interpretation',
      accessor: (r) => <span className="text-xs text-gray-700">{correlationLabel(r.interpretation)}</span>,
    },
    {
      key: 'flags',
      header: 'Flags',
      accessor: (r) => r.flags.length === 0
        ? <span className="text-xs text-gray-400">—</span>
        : (
          <div className="flex flex-col gap-0.5">
            {r.flags.map((f) => (
              <span key={f} className="inline-flex items-center gap-1 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-1.5 py-0.5">
                <AlertTriangle size={10} aria-hidden="true" />{FLAG_LABELS[f] ?? f}
              </span>
            ))}
          </div>
        ),
    },
  ];
}

// ─── Scatter panel ────────────────────────────────────────────────────────────

function ScatterPanel({ course }: { course: CorrelationResult }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-start gap-3 flex-wrap">
        <StatCard title="Pearson r" value={formatCorrelation(course.pearsonCorrelation)} subtitle={correlationLabel(course.interpretation)} accent="blue" className="flex-1 min-w-[140px]" />
        <StatCard title="Internal Avg" value={formatMarks(course.internalAverage)} accent="purple" className="flex-1 min-w-[120px]" />
        <StatCard title="External Avg" value={formatMarks(course.externalAverage)} accent="orange" className="flex-1 min-w-[120px]" />
      </div>

      {course.flags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {course.flags.map((f) => (
            <span key={f} className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-800 bg-amber-50 border border-amber-200 rounded-full px-2.5 py-1">
              <AlertTriangle size={11} aria-hidden="true" />{FLAG_LABELS[f] ?? f}
            </span>
          ))}
        </div>
      )}

      <ChartCard
        title={`${course.courseCode} — Internal vs External Scatter`}
        subtitle={`${course.studentCount} students · r = ${formatCorrelation(course.pearsonCorrelation)}`}
        isEmpty={course.scatterData.length === 0}
        minHeight={300}
      >
        <ResponsiveContainer width="100%" height={300}>
          <ScatterChart margin={{ top: 8, right: 16, left: -8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              type="number"
              dataKey="internalMarks"
              name="Internal Marks"
              domain={[0, 30]}
              label={{ value: 'Internal Marks', position: 'insideBottom', offset: -4, fontSize: 11 }}
              tick={{ fontSize: 10 }}
            />
            <YAxis
              type="number"
              dataKey="externalMarks"
              name="External Marks"
              domain={[0, 75]}
              label={{ value: 'External Marks', angle: -90, position: 'insideLeft', offset: 12, fontSize: 11 }}
              tick={{ fontSize: 10 }}
            />
            <ZAxis range={[30, 30]} />
            <Tooltip
              cursor={{ strokeDasharray: '3 3' }}
              content={({ payload }) => {
                if (!payload?.length) return null;
                const d = payload[0].payload as { internalMarks: number; externalMarks: number; rollNumber: string };
                return (
                  <div className="bg-white border border-gray-200 rounded shadow-sm px-2.5 py-1.5 text-xs">
                    <div className="font-mono text-gray-500 mb-1">{d.rollNumber}</div>
                    <div>Internal: <strong>{d.internalMarks}</strong></div>
                    <div>External: <strong>{d.externalMarks}</strong></div>
                  </div>
                );
              }}
            />
            <ReferenceLine
              x={course.internalAverage}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              label={{ value: 'Int. Avg', fontSize: 9, fill: '#94a3b8' }}
            />
            <ReferenceLine
              y={course.externalAverage}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              label={{ value: 'Ext. Avg', fontSize: 9, fill: '#94a3b8', position: 'insideTopRight' }}
            />
            <Scatter data={course.scatterData} fill="#3b82f6" fillOpacity={0.65} />
          </ScatterChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function CorrelationAnalysis() {
  const [filters, setFilters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const [selected, setSelected] = useState<CorrelationResult | null>(null);
  const { data, loading, error, isNetworkError, retry } = useCorrelation(filters);

  const columns = buildColumns((c) => setSelected(c));

  const strongCount  = data?.filter((c) => (c.pearsonCorrelation ?? 0) >= 0.7).length  ?? 0;
  const flaggedCount = data?.filter((c) => c.flags.length > 0).length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Internal vs External Correlation"
        description="Statistical relationship between internal assessment and external examination marks per course."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Internal vs External' }]}
      />

      <FilterBar
        filters={filters}
        onChange={(u) => setFilters((f) => ({ ...f, ...u }))}
        show={{ academicYear: true, semester: true, department: true }}
      />

      {/* Methodology note */}
      <div className="flex items-start gap-2.5 bg-blue-50 border border-blue-200 rounded-md px-4 py-3" role="note">
        <Info size={15} className="text-blue-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <p className="text-xs text-blue-800">
          Pearson correlation (r) measures the linear association between internal and external marks.
          A strong positive correlation indicates students who perform well internally tend to perform
          well externally. <strong>Correlation indicates association, not causation.</strong> Unusual
          patterns (high internal / low external) may reflect assessment-design issues or examination
          difficulty variation and warrant further review.
        </p>
      </div>

      {/* KPIs */}
      {!loading && data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard title="Courses Analysed" value={data.length} accent="blue" />
          <StatCard title="Strong Correlation" value={strongCount} subtitle="r ≥ 0.7" accent="green" />
          <StatCard title="Flagged Courses" value={flaggedCount} subtitle="unusual patterns" accent={flaggedCount > 0 ? 'orange' : 'green'} />
          <StatCard
            title="Avg Pearson r"
            value={data.length ? formatCorrelation(data.reduce((s, c) => s + (c.pearsonCorrelation ?? 0), 0) / data.length) : '—'}
            accent="purple"
          />
        </div>
      )}

      {/* Scatter for selected course */}
      {selected && (
        <section className="bg-white rounded-lg border border-gray-200 shadow-sm p-4" aria-label="Scatter plot">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-800">Scatter Plot — {selected.courseCode}</h2>
            <button
              onClick={() => setSelected(null)}
              className="text-xs text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-1"
            >
              Close ✕
            </button>
          </div>
          <ScatterPanel course={selected} />
        </section>
      )}

      {/* Table */}
      {error ? (
        <ErrorState message={error} isNetworkError={isNetworkError} onRetry={retry} />
      ) : loading ? (
        <TableSkeleton rows={4} cols={7} />
      ) : !data?.length ? (
        <EmptyState title="No correlation data" description="No internal/external mark data is available for the selected filters." />
      ) : (
        <DataTable
          columns={columns}
          data={data}
          rowKey={(r) => r.courseCode}
          caption="Internal vs external correlation table"
          paginate={false}
        />
      )}
    </div>
  );
}
