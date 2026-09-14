import { Info } from 'lucide-react';
import { useState } from 'react';
import {
  CartesianGrid, Legend, Line, LineChart,
  ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { ChartCard } from '@/components/common/ChartCard';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { StatCard } from '@/components/common/StatCard';
import { ChartSkeleton } from '@/components/common/LoadingSkeleton';
import { useHistorical } from '@/hooks/useAnalysis';
import type { HistoricalComparison } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import { formatDeviation, formatPercentage, trendLabel } from '@/utils/formatters';
import { CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER } from '@/utils/constants';

const DEFAULT_FILTERS: ResultFilters = {
  academicYear: CURRENT_ACADEMIC_YEAR,
  semester: CURRENT_SEMESTER,
  department: CURRENT_DEPARTMENT,
};

const METRIC_TABS = [
  { key: 'passRate',    label: 'Pass Rate %',    unit: '%' },
  { key: 'averageMarks',label: 'Average Marks',   unit: '' },
  { key: 'averageGpa',  label: 'Average GPA',     unit: '' },
  { key: 'failureRate', label: 'Failure Rate %',  unit: '%' },
] as const;

type MetricKey = typeof METRIC_TABS[number]['key'];

const TREND_ICON: Record<string, string> = {
  IMPROVING: '↑',
  DECLINING: '↓',
  STABLE: '→',
  UNKNOWN: '–',
};

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'];

function CourseTrendCard({
  comparison,
  metric,
  color,
}: {
  comparison: HistoricalComparison;
  metric: MetricKey;
  color: string;
}) {
  const points = comparison.dataPoints.map((p) => ({
    label: p.label,
    value: p[metric],
  }));

  const isEmpty = points.length === 0;
  const avgValue = comparison.historicalAverage;

  return (
    <ChartCard
      title={`${comparison.courseCode} — ${comparison.courseName}`}
      subtitle={`Trend: ${TREND_ICON[comparison.trend]} ${trendLabel(comparison.trend)}`}
      isEmpty={isEmpty}
      emptyMessage="No historical data available for this course."
      minHeight={220}
    >
      <div className="flex items-center gap-4 mb-3 flex-wrap">
        <div>
          <div className="text-xs text-gray-500">Current</div>
          <div className="text-sm font-semibold text-gray-900">{formatPercentage(comparison.currentValue)}</div>
        </div>
        {comparison.previousValue != null && (
          <div>
            <div className="text-xs text-gray-500">Previous</div>
            <div className="text-sm font-semibold text-gray-700">{formatPercentage(comparison.previousValue)}</div>
          </div>
        )}
        {comparison.deviationFromAverage != null && (
          <div>
            <div className="text-xs text-gray-500">vs Hist. Avg</div>
            <div className={`text-sm font-semibold ${comparison.deviationFromAverage >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>
              {formatDeviation(comparison.deviationFromAverage)}
            </div>
          </div>
        )}
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${
          comparison.trend === 'IMPROVING' ? 'bg-green-50 border-green-200 text-green-700' :
          comparison.trend === 'DECLINING' ? 'bg-red-50 border-red-200 text-red-700' :
          'bg-gray-100 border-gray-200 text-gray-600'
        }`}>
          {trendLabel(comparison.trend)}
        </span>
      </div>

      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={points} margin={{ top: 4, right: 16, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="label" tick={{ fontSize: 9 }} interval={0} />
          <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} unit="%" />
          <Tooltip formatter={(v: any) => [`${Number(v).toFixed(1)}%`]} contentStyle={{ fontSize: 12 }} />
          {avgValue != null && (
            <ReferenceLine
              y={avgValue}
              stroke="#94a3b8"
              strokeDasharray="4 4"
              label={{ value: 'Hist. Avg', fontSize: 9, fill: '#94a3b8', position: 'insideTopRight' }}
            />
          )}
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
            name="Pass Rate %"
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

export default function HistoricalTrends() {
  const [filters, setFilters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const [metric, setMetric] = useState<MetricKey>('passRate');
  const { data, loading, error, isNetworkError, retry } = useHistorical(filters);

  const declining = data?.filter((c) => c.trend === 'DECLINING').length ?? 0;
  const improving = data?.filter((c) => c.trend === 'IMPROVING').length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Historical Trends"
        description="Longitudinal analysis of course and department performance across semesters."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Historical Trends' }]}
      />

      <FilterBar
        filters={filters}
        onChange={(u) => setFilters((f) => ({ ...f, ...u }))}
        show={{ department: true, programme: true }}
      />

      {/* Data integrity note */}
      <div className="flex items-start gap-2 bg-blue-50 border border-blue-200 rounded-md px-4 py-3" role="note">
        <Info size={14} className="text-blue-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <p className="text-xs text-blue-800">
          Historical charts only show semesters for which result data has been ingested.
          Missing historical data is shown as empty state — no values are fabricated.
        </p>
      </div>

      {/* KPIs */}
      {!loading && data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard title="Courses with Trends" value={data.length} accent="blue" />
          <StatCard title="Improving" value={improving} subtitle="above historical avg" accent="green" />
          <StatCard title="Declining" value={declining} subtitle="below historical avg" accent={declining > 0 ? 'red' : 'green'} />
          <StatCard
            title="Largest Decline"
            value={data.length ? formatDeviation(Math.min(...data.map((c) => c.deviationFromAverage ?? 0))) : '—'}
            accent={declining > 0 ? 'red' : 'gray'}
          />
        </div>
      )}

      {/* Metric tabs */}
      <div className="flex gap-1 border-b border-gray-200" role="tablist" aria-label="Historical metric">
        {METRIC_TABS.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={metric === tab.key}
            onClick={() => setMetric(tab.key)}
            className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-t ${
              metric === tab.key
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Combined trend chart */}
      {!loading && data && data.length > 0 && (
        <ChartCard title="All Courses — Pass Rate Trend" subtitle="Historical comparison" minHeight={260}>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis
                dataKey="label"
                type="category"
                allowDuplicatedCategory={false}
                tick={{ fontSize: 9 }}
              />
              <YAxis domain={[40, 100]} tick={{ fontSize: 10 }} unit="%" />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {data.map((course, i) => (
                <Line
                  key={course.courseCode}
                  data={course.dataPoints.map((p) => ({ label: p.label, value: p[metric] }))}
                  type="monotone"
                  dataKey="value"
                  name={course.courseCode}
                  stroke={COLORS[i % COLORS.length]}
                  strokeWidth={1.5}
                  dot={{ r: 2 }}
                  activeDot={{ r: 4 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Per-course cards */}
      {error ? (
        <ErrorState message={error} isNetworkError={isNetworkError} onRetry={retry} />
      ) : loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <ChartSkeleton key={i} height={280} />)}
        </div>
      ) : !data?.length ? (
        <EmptyState
          title="No historical data available"
          description="No historical records are available for this selection. Historical data becomes available as more semesters are ingested."
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.map((comparison, i) => (
            <CourseTrendCard
              key={comparison.courseCode}
              comparison={comparison}
              metric={metric}
              color={COLORS[i % COLORS.length]}
            />
          ))}
        </div>
      )}
    </div>
  );
}
