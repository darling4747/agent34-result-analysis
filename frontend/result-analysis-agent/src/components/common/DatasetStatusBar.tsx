import { Database, UploadCloud } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useDataset } from '@/hooks/useDataset';
import { useDatasetContext } from '@/contexts/DatasetContext';
import { formatDateTime } from '@/utils/formatters';

export function DatasetStatusBar() {
  const { refreshKey } = useDatasetContext();
  const { datasetInfo, loading } = useDataset(refreshKey);

  if (loading) return null;

  if (!datasetInfo?.has_data) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-blue-50 border-b border-blue-200 text-blue-800 text-xs" role="status">
        <Database size={13} className="flex-shrink-0" aria-hidden="true" />
        <span>No result dataset uploaded yet.</span>
        <Link to="/upload" className="ml-1 font-medium underline hover:text-blue-900 focus:outline-none focus:ring-1 focus:ring-blue-500">
          Upload Results
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 px-4 py-1.5 bg-gray-50 border-b border-gray-200 text-xs text-gray-600 flex-wrap" role="status" aria-label="Current dataset">
      <div className="flex items-center gap-1.5">
        <Database size={12} className="text-blue-500" aria-hidden="true" />
        <span className="font-medium text-gray-800">
          {datasetInfo.academic_year} {datasetInfo.semester ? `Sem ` : ''}
        </span>
      </div>
      <span className="text-gray-400">|</span>
      <span>{datasetInfo.student_count.toLocaleString('en-IN')} students</span>
      <span className="text-gray-400">·</span>
      <span>{datasetInfo.result_count.toLocaleString('en-IN')} results</span>
      <span className="text-gray-400">·</span>
      <span>{datasetInfo.course_count} courses</span>
      {datasetInfo.uploaded_at && (
        <>
          <span className="text-gray-400">·</span>
          <span>Imported {formatDateTime(datasetInfo.uploaded_at)}</span>
        </>
      )}
      <Link to="/upload" className="ml-auto flex items-center gap-1 text-blue-600 hover:text-blue-800 focus:outline-none" aria-label="Upload new dataset">
        <UploadCloud size={11} aria-hidden="true" />
        Upload new
      </Link>
    </div>
  );
}
