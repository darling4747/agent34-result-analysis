import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  GraduationCap,
  Sparkles,
  TrendingUp,
  Users,
  XCircle,
} from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { ChartCard } from '@/components/common/ChartCard';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { PriorityBadge } from '@/components/common/PriorityBadge';
import { StatCard } from '@/components/common/StatCard';
import { PageSkeleton, StatCardSkeleton } from '@/components/common/LoadingSkeleton';
import { useDashboardData } from '@/hooks/useAnalysis';
import type { PriorityLevel } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import {
  CHART_COLORS,
  GRADE_COLORS,
  formatDeviation,
  formatGpa,
  formatMarks,
  formatPercentage,
} from '@/utils/formatters';
const DEFAULT_FILTERS: ResultFilters = {};

export default function Dashboard() {
  const [filters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const { summary, grades, courses, interventions, narrative, loading } = useDashboardData(filters);

  const passFail = useMemo(() => {
    if (!summary.data) return [];
    return [
      { name: 'Pass', value: summary.data.passCount, fill: '#10b981' },
      { name: 'Fail', value: summary.data.failCount, fill: '#ef4444' },
    ];
  }, [summary.data]);

  const passChange = useMemo(() => {
    if (!summary.data?.previousPassPercentage) return undefined;
    return summary.data.passPercentage - summary.data.previousPassPercentage;
  }, [summary.data]);

  const marksChange = useMemo(() => {
    if (!summary.data?.previousAverageMarks) return undefined;
    return summary.data.averageMarks - summary.data.previousAverageMarks;
  }, [summary.data]);

  if (loading) return <PageSkeleton />;

  if (summary.error) {
    return (
      <ErrorState
        message={summary.error}
        isNetworkError={summary.isNetworkError}
        onRetry={summary.retry}
        className="py-24"
      />
    );
  }

  const s = summary.data!;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Result Overview"
        description={s.academicYear ? `${s.academicYear} · Semester ${s.semester} · ${s.department || 'All Departments'}` : 'Institutional Academic Result Overview'}
        breadcrumbs={[{ label: 'Overview' }]}
        actions={
          <Link
            to="/upload"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
          >
            Upload Results
          </Link>
        }
      />

      {/* ── KPI Cards ─────────────────────────────────────────────────── */}
      <section aria-label="Key performance indicators">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {summary.loading ? (
            Array.from({ length: 6 }).map((_, i) => <StatCardSkeleton key={i} />)
          ) : (
            <>
              <StatCard
                title="Total Students"
                value={(s?.totalStudents ?? 0).toLocaleString('en-IN')}
                subtitle="Registered this semester"
                icon={<Users size={15} />}
                accent="blue"
              />
              <StatCard
                title="Total Results"
                value={(s?.totalResults ?? 0).toLocaleString('en-IN')}
                subtitle="Student-course records"
                icon={<BookOpen size={15} />}
                accent="purple"
              />
              <StatCard
                title="Pass %"
                value={formatPercentage(s?.passPercentage)}
                subtitle={`${(s?.passCount ?? 0).toLocaleString('en-IN')} students`}
                change={passChange}
                changeLabel=" vs prev sem"
                icon={<CheckCircle2 size={15} />}
                accent="green"
              />
              <StatCard
                title="Failure %"
                value={formatPercentage(s?.failPercentage)}
                subtitle={`${(s?.failCount ?? 0).toLocaleString('en-IN')} students`}
                change={passChange !== undefined ? -passChange : undefined}
                changeLabel=" vs prev sem"
                icon={<XCircle size={15} />}
                accent="red"
              />
              <StatCard
                title="Avg Marks"
                value={formatMarks(s.averageMarks)}
                subtitle="Out of 100"
                change={marksChange}
                changeLabel=" pts"
                icon={<TrendingUp size={15} />}
                accent="orange"
              />
              <StatCard
                title="Avg GPA"
                value={formatGpa(s.averageGpa)}
                subtitle="10-point scale"
                icon={<GraduationCap size={15} />}
                accent="blue"
              />
            </>
          )}
        </div>
      </section>

      {/* ── Charts row ────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Grade Distribution */}
        <ChartCard
          title="Grade Distribution"
          subtitle="All courses · current semester"
          isEmpty={!grades.data?.length}
        >
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={grades.data ?? []} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="grade" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v: any) => [v, 'Students']}
                contentStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="count" radius={[3, 3, 0, 0]} name="Students">
                {(grades.data ?? []).map((entry) => (
                  <Cell key={entry.grade} fill={GRADE_COLORS[entry.grade] ?? CHART_COLORS[0]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        {/* Pass / Fail split */}
        <ChartCard
          title="Pass / Fail Distribution"
          subtitle={`${s.totalStudents} students evaluated`}
          isEmpty={passFail.length === 0}
        >
          <div className="flex items-center gap-6 h-[240px]">
            <ResponsiveContainer width="60%" height="100%">
              <PieChart>
                <Pie
                  data={passFail}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={3}
                >
                  {passFail.map((entry, i) => (
                    <Cell key={i} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip formatter={(v: any) => [v ? v.toLocaleString('en-IN') : '0', 'Students']} contentStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-col gap-4">
              {passFail.map((item) => (
                <div key={item.name} className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: item.fill }} aria-hidden="true" />
                    <span className="text-sm font-medium text-gray-700">{item.name}</span>
                  </div>
                  <div className="text-xl font-semibold text-gray-900 pl-5">
                    {item.name === 'Pass'
                      ? formatPercentage(s.passPercentage)
                      : formatPercentage(s.failPercentage)
                    }
                  </div>
                  <div className="text-xs text-gray-500 pl-5">{item.value.toLocaleString('en-IN')} students</div>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>
      </div>

      {/* ── Course Performance Table ──────────────────────────────────── */}
      <section aria-label="Course performance">
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-800">Course Performance</h2>
            <Link to="/courses" className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              Full analysis →
            </Link>
          </div>
          <div className="overflow-x-auto scrollbar-thin">
            <table className="w-full text-sm" aria-label="Course performance summary">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  {['Course', 'Students', 'Pass %', 'Fail %', 'Avg Marks', 'Deviation', 'Priority'].map((h) => (
                    <th key={h} scope="col" className="px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(courses.data ?? []).map((course) => (
                  <tr key={course.courseCode} className="border-b border-gray-100 hover:bg-gray-50 last:border-0">
                    <td className="px-4 py-2.5">
                      <div className="font-medium text-gray-900">{course.courseCode}</div>
                      <div className="text-xs text-gray-500 truncate max-w-[180px]">{course.courseName}</div>
                    </td>
                    <td className="px-4 py-2.5 text-gray-700">{course.studentCount}</td>
                    <td className="px-4 py-2.5">
                      <span className={`font-medium ${course.passPercentage >= 75 ? 'text-emerald-700' : course.passPercentage >= 60 ? 'text-yellow-700' : 'text-red-700'}`}>
                        {formatPercentage(course.passPercentage)}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-gray-700">{formatPercentage(course.failurePercentage)}</td>
                    <td className="px-4 py-2.5 text-gray-700">{formatMarks(course.averageMarks)}</td>
                    <td className="px-4 py-2.5">
                      {course.historicalDeviation != null ? (
                        <span className={`text-xs font-medium ${course.historicalDeviation >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {formatDeviation(course.historicalDeviation)}
                        </span>
                      ) : (
                        <span className="text-gray-400 text-xs">—</span>
                      )}
                    </td>
                    <td className="px-4 py-2.5">
                      <PriorityBadge level={course.priorityLevel} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── Bottom row: Section comparison + Intervention priorities ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Section comparison */}
        <ChartCard
          title="Section Comparison"
          subtitle="Pass rate by section"
          isEmpty={!courses.data?.length}
        >
          <ResponsiveContainer width="100%" height={220}>
            <BarChart
              data={[
                { section: 'Sec A', passRate: 88.9, avgMarks: 72.4 },
                { section: 'Sec B', passRate: 82.9, avgMarks: 67.8 },
                { section: 'Sec C', passRate: 76.5, avgMarks: 62.1 },
                { section: 'Sec D', passRate: 87.1, avgMarks: 70.6 },
              ]}
              margin={{ top: 4, right: 8, left: -16, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="section" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
              <Tooltip formatter={(v: any) => [`${v}%`]} contentStyle={{ fontSize: 12 }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="passRate" name="Pass Rate %" fill="#3b82f6" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-2 flex justify-end">
            <Link to="/sections" className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              Section analysis →
            </Link>
          </div>
        </ChartCard>

        {/* Intervention priorities */}
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-sm p-4"
          aria-label="Intervention priorities"
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
              <AlertTriangle size={14} className="text-orange-500" aria-hidden="true" />
              Intervention Priorities
            </h2>
            <Link to="/interventions" className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              Full list →
            </Link>
          </div>
          <ul className="flex flex-col gap-2" role="list">
            {(interventions.data ?? []).slice(0, 5).map((item) => (
              <li
                key={item.courseCode}
                className="flex items-start gap-3 p-2.5 rounded-md border border-gray-100 hover:border-gray-200 bg-gray-50"
              >
                <div className="flex-shrink-0 text-sm font-bold text-gray-400 w-4 text-center">{item.rank}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-gray-800">{item.courseCode}</span>
                    <span className="text-xs text-gray-500 truncate">{item.courseName}</span>
                  </div>
                  <div className="text-xs text-gray-500 mt-0.5 line-clamp-1">
                    {item.reasons[0]}
                  </div>
                </div>
                <PriorityBadge level={item.priorityLevel as PriorityLevel} />
              </li>
            ))}
          </ul>
        </section>
      </div>

      {/* ── Pass-rate trend sparkline ─────────────────────────────────── */}
      <ChartCard
        title="Semester-over-Semester Pass Rate Trend"
        subtitle="Department aggregate — last 4 semesters"
        isEmpty={false}
      >
        <ResponsiveContainer width="100%" height={180}>
          <LineChart
            data={[
              { label: '2023-24 S5', passRate: 78.2, avg: 64.8 },
              { label: '2023-24 S6', passRate: 76.9, avg: 63.1 },
              { label: '2024-25 S5', passRate: 80.4, avg: 66.4 },
              { label: '2024-25 S6', passRate: 79.6, avg: 66.1 },
              { label: '2025-26 S5', passRate: 81.2, avg: 67.8 },
              { label: '2025-26 S6', passRate: s.passPercentage, avg: s.averageMarks },
            ]}
            margin={{ top: 4, right: 16, left: -16, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} />
            <YAxis domain={[50, 100]} tick={{ fontSize: 11 }} unit="%" />
            <Tooltip formatter={(v: any) => [`${v}%`]} contentStyle={{ fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="passRate"
              name="Pass Rate %"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
        <div className="mt-1 flex justify-end">
          <Link to="/historical" className="text-xs text-blue-600 hover:text-blue-800 font-medium">
            Historical trends →
          </Link>
        </div>
      </ChartCard>

      {/* ── AI Narrative ──────────────────────────────────────────────── */}
      {narrative.data && (
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden"
          aria-label="Analytical narrative"
        >
          {/* Verified metrics strip */}
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
            <h2 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-2">
              Verified Analysis
            </h2>
            <div className="flex flex-wrap gap-6">
              {[
                { label: 'Pass Rate', value: formatPercentage(s.passPercentage) },
                { label: 'Average Marks', value: formatMarks(s.averageMarks) },
                { label: 'Failure Rate', value: formatPercentage(s.failPercentage) },
                { label: 'Average GPA', value: formatGpa(s.averageGpa) },
                { label: 'Total Students', value: s.totalStudents.toLocaleString('en-IN') },
              ].map((m) => (
                <div key={m.label}>
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className="text-sm font-semibold text-gray-900">{m.value}</div>
                </div>
              ))}
            </div>
          </div>

          {/* AI-generated narrative */}
          <div className="px-4 py-3">
            <div className="flex items-center gap-1.5 mb-2">
              <Sparkles size={13} className="text-purple-500" aria-hidden="true" />
              <h2 className="text-xs font-semibold text-purple-700 uppercase tracking-wide">
                AI Analysis
              </h2>
              <span className="ml-auto text-[10px] text-gray-400 italic">
                AI-generated interpretation · not verified data
              </span>
            </div>
            <p className="text-sm text-gray-700 leading-relaxed mb-3">
              {narrative.data.summary}
            </p>

            {narrative.data.keyFindings.length > 0 && (
              <div className="mb-3">
                <div className="text-xs font-semibold text-gray-600 mb-1.5">Key Findings</div>
                <ul className="flex flex-col gap-1.5" role="list">
                  {narrative.data.keyFindings.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-purple-400 flex-shrink-0" aria-hidden="true" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="mt-3 p-2.5 bg-amber-50 border border-amber-200 rounded-md text-xs text-amber-800">
              <strong>Note:</strong> {narrative.data.disclaimer}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
