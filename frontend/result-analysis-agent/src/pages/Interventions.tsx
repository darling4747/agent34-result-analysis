import { AlertTriangle, ChevronDown, ChevronUp, Info } from 'lucide-react';
import { useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, Cell,
  ResponsiveContainer, Tooltip, XAxis, YAxis,
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
import { useInterventions, useInterventionSummary } from '@/hooks/useAnalysis';
import type { InterventionCourse } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import { formatDeviation, formatPercentage, priorityDotClass } from '@/utils/formatters';
import { CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER } from '@/utils/constants';

const DEFAULT_FILTERS: ResultFilters = {
  academicYear: CURRENT_ACADEMIC_YEAR,
  semester: CURRENT_SEMESTER,
  department: CURRENT_DEPARTMENT,
};

const PRIORITY_COLORS: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#f59e0b',
  LOW:      '#10b981',
};

// ─── Expandable reason row ────────────────────────────────────────────────────

function ReasonList({ reasons }: { reasons: string[] }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? reasons : reasons.slice(0, 1);

  return (
    <div className="flex flex-col gap-1">
      {visible.map((r, i) => (
        <div key={i} className="flex items-start gap-1.5 text-xs text-gray-700">
          <span className="mt-1 w-1 h-1 rounded-full bg-gray-400 flex-shrink-0" aria-hidden="true" />
          {r}
        </div>
      ))}
      {reasons.length > 1 && (
        <button
          onClick={() => setExpanded((e) => !e)}
          className="inline-flex items-center gap-0.5 text-xs text-blue-600 hover:text-blue-800 mt-0.5 focus:outline-none focus:ring-1 focus:ring-blue-500 rounded"
        >
          {expanded
            ? <><ChevronUp size={11} />Show less</>
            : <><ChevronDown size={11} />+{reasons.length - 1} more reason{reasons.length - 1 > 1 ? 's' : ''}</>
          }
        </button>
      )}
    </div>
  );
}

// ─── Columns ──────────────────────────────────────────────────────────────────

const COLUMNS: Column<InterventionCourse>[] = [
  {
    key: 'rank',
    header: '#',
    accessor: (r) => <span className="text-sm font-bold text-gray-500">{r.rank}</span>,
    sortValue: (r) => r.rank,
    width: '48px',
  },
  {
    key: 'course',
    header: 'Course',
    accessor: (r) => (
      <div>
        <div className="font-medium text-gray-900">{r.courseCode}</div>
        <div className="text-xs text-gray-500 max-w-[180px] truncate">{r.courseName}</div>
        <div className="text-xs text-gray-400 mt-0.5">{r.faculty}</div>
      </div>
    ),
    sortValue: (r) => r.courseCode,
  },
  {
    key: 'failRate',
    header: 'Failure Rate',
    accessor: (r) => (
      <span className={`font-medium ${r.failureRate >= 30 ? 'text-red-700' : r.failureRate >= 20 ? 'text-orange-700' : 'text-yellow-700'}`}>
        {formatPercentage(r.failureRate)}
      </span>
    ),
    sortValue: (r) => r.failureRate,
  },
  {
    key: 'histDev',
    header: 'Hist. Δ',
    accessor: (r) => r.historicalDeviation != null
      ? <span className={`text-xs font-medium ${r.historicalDeviation >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatDeviation(r.historicalDeviation)}</span>
      : <span className="text-gray-400 text-xs">—</span>,
    sortValue: (r) => r.historicalDeviation ?? 0,
  },
  {
    key: 'secDev',
    header: 'Section Δ',
    accessor: (r) => r.sectionDeviation != null
      ? <span className={`text-xs font-medium ${r.sectionDeviation >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{formatDeviation(r.sectionDeviation)}</span>
      : <span className="text-gray-400 text-xs">—</span>,
    sortValue: (r) => r.sectionDeviation ?? 0,
  },
  {
    key: 'ieGap',
    header: 'I/E Gap',
    accessor: (r) => r.internalExternalGap != null ? formatDeviation(r.internalExternalGap) : <span className="text-gray-400 text-xs">—</span>,
    sortValue: (r) => r.internalExternalGap ?? 0,
  },
  {
    key: 'score',
    header: 'Priority Score',
    accessor: (r) => (
      <div className="flex items-center gap-1.5">
        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden" aria-hidden="true">
          <div className="h-full rounded-full" style={{ width: `${r.priorityScore}%`, background: PRIORITY_COLORS[r.priorityLevel] }} />
        </div>
        <span className="text-xs font-mono text-gray-700">{r.priorityScore.toFixed(0)}</span>
      </div>
    ),
    sortValue: (r) => r.priorityScore,
  },
  { key: 'level', header: 'Priority', accessor: (r) => <PriorityBadge level={r.priorityLevel} />, sortValue: (r) => r.priorityScore },
  { key: 'reasons', header: 'Reason', accessor: (r) => <ReasonList reasons={r.reasons} /> },
];

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Interventions() {
  const [filters, setFilters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const { data, loading, error, isNetworkError, retry } = useInterventions(filters);
  const { data: summary } = useInterventionSummary(filters);

  const chartData = data?.map((c) => ({
    course: c.courseCode,
    score: c.priorityScore,
    level: c.priorityLevel,
  })) ?? [];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Intervention Priorities"
        description="Courses requiring departmental attention, ranked by composite priority score."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Interventions' }]}
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
          Priority score is computed from failure rate, deviation from historical baseline, section
          performance deviation, and internal/external mark gap. <strong>Failure rate alone does not
          determine priority.</strong> A course with a historically high failure rate may score
          lower than one with a sudden unexpected decline.
        </p>
      </div>

      {/* Summary KPIs */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {[
            { label: 'Total Flagged', value: summary.total,    accent: 'blue' as const, dot: '' },
            { label: 'Critical',      value: summary.critical, accent: 'red' as const,    dot: PRIORITY_COLORS.CRITICAL },
            { label: 'High',          value: summary.high,     accent: 'orange' as const, dot: PRIORITY_COLORS.HIGH },
            { label: 'Medium',        value: summary.medium,   accent: 'orange' as const, dot: PRIORITY_COLORS.MEDIUM },
            { label: 'Low',           value: summary.low,      accent: 'green' as const,  dot: PRIORITY_COLORS.LOW },
          ].map((item) => (
            <StatCard key={item.label} title={item.label} value={item.value} accent={item.accent} />
          ))}
        </div>
      )}

      {/* Priority distribution chart */}
      {!loading && chartData.length > 0 && (
        <ChartCard title="Priority Score by Course" subtitle="Higher score = higher urgency" minHeight={200}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData} margin={{ top: 4, right: 16, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="course" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Tooltip
                formatter={(v: any) => [Number(v).toFixed(1), 'Priority Score']}
                contentStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="score" name="Priority Score" radius={[3, 3, 0, 0]}>
                {chartData.map((c) => (
                  <Cell key={c.course} fill={PRIORITY_COLORS[c.level] ?? '#6b7280'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Priority distribution legend */}
      {!loading && data && (
        <div className="flex flex-wrap gap-3">
          {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((level) => {
            const count = data.filter((c) => c.priorityLevel === level).length;
            return (
              <div key={level} className="flex items-center gap-1.5 text-xs text-gray-600">
                <span className={`w-2.5 h-2.5 rounded-full ${priorityDotClass(level)}`} aria-hidden="true" />
                {level}: <strong>{count}</strong>
              </div>
            );
          })}
        </div>
      )}

      {/* Table */}
      {error ? (
        <ErrorState message={error} isNetworkError={isNetworkError} onRetry={retry} />
      ) : loading ? (
        <TableSkeleton rows={5} cols={8} />
      ) : !data?.length ? (
        <EmptyState
          title="No intervention priorities detected"
          description="No courses were flagged for intervention under the selected filters."
          icon={<AlertTriangle size={40} strokeWidth={1.5} />}
        />
      ) : (
        <DataTable
          columns={COLUMNS}
          data={data}
          rowKey={(r) => r.courseCode}
          caption="Intervention priority table"
          paginate={false}
        />
      )}
    </div>
  );
}
