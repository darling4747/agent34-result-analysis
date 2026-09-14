import { Medal, Printer, Trophy } from 'lucide-react';
import { useState } from 'react';
import { DataTable, type Column } from '@/components/common/DataTable';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { ExportButton } from '@/components/common/ExportButton';
import { FilterBar } from '@/components/common/FilterBar';
import { PageHeader } from '@/components/common/PageHeader';
import { StatCard } from '@/components/common/StatCard';
import { TableSkeleton } from '@/components/common/LoadingSkeleton';
import { useMeritList } from '@/hooks/useAnalysis';
import type { MeritEntry, MeritScope } from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import { formatGpa, formatMarks } from '@/utils/formatters';
import { CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER } from '@/utils/constants';

const DEFAULT_FILTERS: ResultFilters = {
  academicYear: CURRENT_ACADEMIC_YEAR,
  semester: CURRENT_SEMESTER,
  department: CURRENT_DEPARTMENT,
};

const STATUS_STYLE: Record<string, string> = {
  DISTINCTION: 'bg-purple-100 text-purple-800 border-purple-200',
  FIRST_CLASS: 'bg-blue-100 text-blue-800 border-blue-200',
  SECOND_CLASS: 'bg-gray-100 text-gray-700 border-gray-200',
  PASS: 'bg-green-100 text-green-800 border-green-200',
};

const STATUS_LABELS: Record<string, string> = {
  DISTINCTION: 'Distinction',
  FIRST_CLASS: 'First Class',
  SECOND_CLASS: 'Second Class',
  PASS: 'Pass',
};

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <Medal size={16} className="text-yellow-500" aria-label="Rank 1 — Gold" />;
  if (rank === 2) return <Medal size={16} className="text-gray-400" aria-label="Rank 2 — Silver" />;
  if (rank === 3) return <Medal size={16} className="text-amber-600" aria-label="Rank 3 — Bronze" />;
  return <span className="text-sm font-semibold text-gray-600">{rank}</span>;
}

const COLUMNS: Column<MeritEntry>[] = [
  { key: 'rank',      header: 'Rank',        accessor: (r) => <RankBadge rank={r.rank} />,                                                                                                              sortValue: (r) => r.rank, width: '60px' },
  { key: 'roll',      header: 'Roll No.',    accessor: (r) => <span className="font-mono text-xs">{r.rollNumber}</span>,                                                                                sortValue: (r) => r.rollNumber },
  { key: 'name',      header: 'Student',     accessor: (r) => <span className="font-medium text-gray-900">{r.studentName}</span>,                                                                      sortValue: (r) => r.studentName },
  { key: 'prog',      header: 'Programme',   accessor: (r) => <span className="text-xs">{r.programme} · {r.branch}</span> },
  { key: 'section',   header: 'Section',     accessor: (r) => `Section ${r.section}`,                                                                                                                   sortValue: (r) => r.section },
  { key: 'batch',     header: 'Batch',       accessor: (r) => r.batch,                                                                                                                                  sortValue: (r) => r.batch },
  { key: 'sgpa',      header: 'SGPA',        accessor: (r) => <span className="font-semibold text-blue-700">{formatGpa(r.sgpa)}</span>,                                                                 sortValue: (r) => r.sgpa },
  { key: 'cgpa',      header: 'CGPA',        accessor: (r) => r.cgpa != null ? formatGpa(r.cgpa) : <span className="text-gray-400 text-xs">—</span>,                                                   sortValue: (r) => r.cgpa ?? 0 },
  { key: 'marks',     header: 'Total Marks', accessor: (r) => formatMarks(r.totalMarks, 0),                                                                                                             sortValue: (r) => r.totalMarks },
  {
    key: 'status',
    header: 'Classification',
    accessor: (r) => (
      <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border ${STATUS_STYLE[r.status] ?? ''}`}>
        {STATUS_LABELS[r.status] ?? r.status}
      </span>
    ),
    sortValue: (r) => r.status,
  },
];

const SCOPE_TABS: Array<{ value: MeritScope | 'ALL'; label: string }> = [
  { value: 'ALL',       label: 'All' },
  { value: 'PROGRAMME', label: 'Programme Toppers' },
  { value: 'SECTION',   label: 'Section Toppers' },
  { value: 'COURSE',    label: 'Course Toppers' },
];

export default function MeritList() {
  const [filters, setFilters] = useState<ResultFilters>(DEFAULT_FILTERS);
  const [scope, setScope] = useState<MeritScope | 'ALL'>('ALL');
  const { data, loading, error, isNetworkError, retry } = useMeritList(filters);

  const filtered = scope === 'ALL' ? (data ?? []) : (data ?? []).filter((e) => e.scope === scope);

  const distinctions = data?.filter((e) => e.status === 'DISTINCTION').length ?? 0;
  const firstClass   = data?.filter((e) => e.status === 'FIRST_CLASS').length  ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Merit List"
        description="Programme, section, and course toppers for the selected semester."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Merit List' }]}
        actions={
          <div className="flex gap-2">
            <ExportButton
              label="Export"
              onExport={async () => { await new Promise((r) => setTimeout(r, 800)); }}
            />
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium border border-gray-200 text-gray-700 bg-white rounded-md hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Print merit list"
            >
              <Printer size={14} aria-hidden="true" />
              Print
            </button>
          </div>
        }
      />

      <FilterBar
        filters={filters}
        onChange={(u) => setFilters((f) => ({ ...f, ...u }))}
        show={{ academicYear: true, semester: true, department: true, programme: true }}
      />

      {/* KPIs */}
      {!loading && data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard title="Toppers Listed" value={data.length} icon={<Trophy size={15} />} accent="blue" />
          <StatCard title="Distinctions" value={distinctions} subtitle="SGPA ≥ 9.0" accent="purple" />
          <StatCard title="First Class" value={firstClass} subtitle="SGPA ≥ 7.5" accent="blue" />
          <StatCard
            title="Top SGPA"
            value={data[0] ? formatGpa(data[0].sgpa) : '—'}
            subtitle={data[0]?.studentName ?? ''}
            accent="green"
          />
        </div>
      )}

      {/* Scope tabs */}
      <div className="flex gap-1 border-b border-gray-200" role="tablist" aria-label="Merit list scope">
        {SCOPE_TABS.map((tab) => (
          <button
            key={tab.value}
            role="tab"
            aria-selected={scope === tab.value}
            onClick={() => setScope(tab.value)}
            className={`px-3 py-2 text-sm font-medium border-b-2 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-t ${
              scope === tab.value
                ? 'border-blue-600 text-blue-700'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.label}
            {tab.value !== 'ALL' && data && (
              <span className="ml-1.5 text-xs text-gray-400">
                ({data.filter((e) => e.scope === tab.value).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Table */}
      {error ? (
        <ErrorState message={error} isNetworkError={isNetworkError} onRetry={retry} />
      ) : loading ? (
        <TableSkeleton rows={10} cols={9} />
      ) : !filtered.length ? (
        <EmptyState
          title="No merit list available"
          description="No merit entries are available for the selected filters and scope."
          icon={<Trophy size={40} strokeWidth={1.5} />}
        />
      ) : (
        <DataTable
          columns={COLUMNS}
          data={filtered}
          rowKey={(r) => `${r.rollNumber}-${r.scope}`}
          searchable
          searchPlaceholder="Search by name or roll number…"
          searchFilter={(r, q) =>
            r.studentName.toLowerCase().includes(q) ||
            r.rollNumber.toLowerCase().includes(q) ||
            r.section.toLowerCase().includes(q)
          }
          caption="Merit list"
          defaultPageSize={20}
        />
      )}
    </div>
  );
}
