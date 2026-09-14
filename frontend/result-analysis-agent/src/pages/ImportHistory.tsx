import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { DataTable, type Column } from '@/components/common/DataTable';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { StatusBadge } from '@/components/common/StatusBadge';
import { TableSkeleton } from '@/components/common/LoadingSkeleton';
import { formatDateTime } from '@/utils/formatters';
import apiClient from '@/api/client';
import { ApiError } from '@/api/client';
import { useEffect } from 'react';

interface ImportRecord {
  id: number;
  filename: string;
  academic_year: string;
  semester: number;
  department: string | null;
  status: string;
  is_active: boolean;
  total_rows: number;
  valid_rows: number;
  rejected_rows: number;
  student_count: number;
  result_count: number;
  course_count: number;
  created_at: string | null;
  completed_at: string | null;
}

export default function ImportHistory() {
  const [data, setData] = useState<ImportRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activatingId, setActivatingId] = useState<number | null>(null);

  const fetchImports = () => {
    setLoading(true);
    apiClient.get('/api/results/imports')
      .then((res) => {
        setData(res.data.data ?? []);
        setError(null);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : 'Failed to load imports.');
      })
      .finally(() => { setLoading(false); });
  };

  useEffect(() => {
    fetchImports();
  }, []);

  const handleActivate = async (id: number) => {
    try {
      setActivatingId(id);
      await apiClient.post(`/api/results/imports/${id}/activate`);
      fetchImports();
    } catch (err) {
      alert(err instanceof ApiError ? err.message : 'Failed to activate dataset.');
    } finally {
      setActivatingId(null);
    }
  };

  const columns: Column<ImportRecord>[] = [
    {
      key: 'filename',
      header: 'File',
      accessor: (r) => (
        <div>
          <div className="font-medium text-gray-900 text-xs font-mono truncate max-w-[200px]">{r.filename}</div>
          <div className="text-xs text-gray-500">{r.academic_year} · Sem {r.semester}</div>
        </div>
      ),
      sortValue: (r) => r.filename,
    },
    { key: 'dept', header: 'Dept', accessor: (r) => r.department ?? '—', sortValue: (r) => r.department ?? '' },
    { key: 'students', header: 'Students', accessor: (r) => (r.student_count || r.valid_rows).toLocaleString('en-IN'), sortValue: (r) => r.student_count },
    { key: 'results', header: 'Results', accessor: (r) => r.result_count.toLocaleString('en-IN'), sortValue: (r) => r.result_count },
    { key: 'courses', header: 'Courses', accessor: (r) => r.course_count, sortValue: (r) => r.course_count },
    { key: 'rejected', header: 'Rejected', accessor: (r) => r.rejected_rows, sortValue: (r) => r.rejected_rows },
    { key: 'status', header: 'Status', accessor: (r) => <StatusBadge status={r.status} />, sortValue: (r) => r.status },
    {
      key: 'active',
      header: 'Dataset State',
      accessor: (r) => r.is_active ? (
        <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2.5 py-0.5">✓ Active Dataset</span>
      ) : r.status === 'COMPLETED' ? (
        <button
          onClick={() => handleActivate(r.id)}
          disabled={activatingId === r.id}
          className="text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-md px-2.5 py-1 transition-colors disabled:opacity-50"
        >
          {activatingId === r.id ? 'Activating...' : 'Set Active'}
        </button>
      ) : (
        <span className="text-gray-400 text-xs">—</span>
      )
    },
    { key: 'uploaded', header: 'Uploaded', accessor: (r) => formatDateTime(r.created_at), sortValue: (r) => r.created_at ?? '' },
  ];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Import History"
        description="All result dataset uploads. The active dataset drives the current dashboard."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Import History' }]}
        actions={
          <Link to="/upload" className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
            Upload New
          </Link>
        }
      />
      {error ? (
        <ErrorState message={error} onRetry={() => { setLoading(true); setError(null); }} />
      ) : loading ? (
        <TableSkeleton rows={5} cols={8} />
      ) : !data.length ? (
        <EmptyState
          title="No uploads yet"
          description="No result datasets have been uploaded. Upload a CSV or Excel file to get started."
          action={<Link to="/upload" className="px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700">Upload Results</Link>}
        />
      ) : (
        <DataTable
          columns={columns}
          data={data}
          rowKey={(r) => String(r.id)}
          caption="Import history"
        />
      )}
    </div>
  );
}
