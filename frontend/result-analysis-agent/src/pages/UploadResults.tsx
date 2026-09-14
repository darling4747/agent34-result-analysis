import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileSpreadsheet,
  Info,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/common/PageHeader';
import { useUpload } from '@/hooks/useResults';
import { useDatasetContext } from '@/contexts/DatasetContext';
import type { IngestionStatus, ValidationIssue } from '@/types/result';
import { ACADEMIC_YEARS, ACCEPTED_FILE_TYPES, CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER, DEPARTMENTS, MAX_FILE_SIZE_MB, SEMESTERS } from '@/utils/constants';

// ─── Pipeline step config ─────────────────────────────────────────────────────

const PIPELINE_STEPS: Array<{ status: IngestionStatus; label: string; description: string }> = [
  { status: 'UPLOADING',   label: 'Upload',      description: 'Transferring file to server' },
  { status: 'VALIDATING',  label: 'Validating',  description: 'Checking records and structure' },
  { status: 'RECONCILING', label: 'Reconciling', description: 'Matching with student master data' },
  { status: 'ANALYZING',   label: 'Analyzing',   description: 'Running result analysis pipeline' },
  { status: 'COMPLETED',   label: 'Completed',   description: 'Analysis ready' },
];

const STATUS_ORDER: IngestionStatus[] = ['UPLOADING', 'VALIDATING', 'RECONCILING', 'ANALYZING', 'COMPLETED'];

function stepIndex(status: IngestionStatus) {
  return STATUS_ORDER.indexOf(status);
}

// ─── Severity helpers ─────────────────────────────────────────────────────────

const SEVERITY_STYLE = {
  ERROR:   { bg: 'bg-red-50',    border: 'border-red-200',   icon: <AlertCircle size={14} className="text-red-500 flex-shrink-0 mt-0.5" />,    badge: 'bg-red-100 text-red-700' },
  WARNING: { bg: 'bg-amber-50',  border: 'border-amber-200', icon: <AlertTriangle size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />, badge: 'bg-amber-100 text-amber-700' },
  INFO:    { bg: 'bg-blue-50',   border: 'border-blue-200',  icon: <Info size={14} className="text-blue-500 flex-shrink-0 mt-0.5" />,           badge: 'bg-blue-100 text-blue-700' },
};

// ─── Validation issue row ─────────────────────────────────────────────────────

function ValidationIssueRow({ issue }: { issue: ValidationIssue }) {
  const [expanded, setExpanded] = useState(false);
  const style = SEVERITY_STYLE[issue.severity];

  return (
    <div className={`rounded-md border ${style.border} ${style.bg} overflow-hidden`}>
      <button
        className="w-full flex items-start gap-2.5 px-3 py-2.5 text-left focus:outline-none focus:ring-2 focus:ring-inset focus:ring-blue-500"
        onClick={() => setExpanded((e) => !e)}
        aria-expanded={expanded}
      >
        {style.icon}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${style.badge}`}>
              {issue.severity}
            </span>
            <span className="text-xs font-medium text-gray-700">{issue.message}</span>
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {issue.count} occurrence{issue.count !== 1 ? 's' : ''}
            {issue.affectedColumns.length > 0 && ` · Columns: ${issue.affectedColumns.join(', ')}`}
          </div>
        </div>
        {issue.affectedRows.length > 0 && (
          <span className="flex-shrink-0 text-gray-400 mt-0.5">
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </span>
        )}
      </button>
      {expanded && issue.affectedRows.length > 0 && (
        <div className="px-3 pb-2.5 pt-0">
          <div className="text-xs text-gray-500">
            Affected rows:{' '}
            <span className="font-mono text-gray-700">
              {issue.affectedRows.slice(0, 20).join(', ')}
              {issue.affectedRows.length > 20 && ` … +${issue.affectedRows.length - 20} more`}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function UploadResults() {
  const [file, setFile]       = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [year, setYear]       = useState(CURRENT_ACADEMIC_YEAR);
  const [sem, setSem]         = useState(CURRENT_SEMESTER);
  const [dept, setDept]       = useState(CURRENT_DEPARTMENT);
  const [fileError, setFileError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { triggerRefresh } = useDatasetContext();
  const { status, percent, message, result, error, upload, reset, validateFile } = useUpload();

  const isActive  = status !== 'IDLE' && status !== 'FAILED';

  // Trigger global refresh when upload completes so all analytics hooks re-fetch
  useEffect(() => { if (status === 'COMPLETED') triggerRefresh(); }, [status, triggerRefresh]);
  const isDone    = status === 'COMPLETED';
  const isFailed  = status === 'FAILED';
  const currentStep = stepIndex(status);

  // ── File selection helpers ───────────────────────────────────────────────

  function handleFileSelect(selected: File | null) {
    if (!selected) return;
    const err = validateFile(selected);
    setFileError(err);
    setFile(err ? null : selected);
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = e.dataTransfer.files[0] ?? null;
    handleFileSelect(dropped);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    handleFileSelect(e.target.files?.[0] ?? null);
    e.target.value = '';
  }

  function handleRemoveFile() {
    setFile(null);
    setFileError(null);
  }

  function handleReset() {
    setFile(null);
    setFileError(null);
    reset();
  }

  async function handleUpload() {
    if (!file) return;
    await upload(file, year, sem, dept);
  }

  // ── Render ────────────────────────────────────────────────────────────────

  const errors   = (result?.validationIssues ?? []).filter((i) => i.severity === 'ERROR');
  const warnings = (result?.validationIssues ?? []).filter((i) => i.severity === 'WARNING');

  return (
    <div className="flex flex-col gap-6 max-w-3xl">
      <PageHeader
        title="Upload Results"
        description="Import semester result data for validation, reconciliation, and analysis."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Upload Results' }]}
      />

      {/* ── Context selectors ──────────────────────────────────────────── */}
      {!isActive && !isDone && (
        <section className="bg-white rounded-lg border border-gray-200 shadow-sm p-4" aria-label="Upload context">
          <h2 className="text-sm font-semibold text-gray-800 mb-3">Result Set Context</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide" htmlFor="upload-year">
                Academic Year
              </label>
              <select
                id="upload-year"
                value={year}
                onChange={(e) => setYear(e.target.value)}
                className="border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {ACADEMIC_YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide" htmlFor="upload-sem">
                Semester
              </label>
              <select
                id="upload-sem"
                value={sem}
                onChange={(e) => setSem(Number(e.target.value))}
                className="border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {SEMESTERS.map((s) => <option key={s} value={s}>Semester {s}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide" htmlFor="upload-dept">
                Department
              </label>
              <select
                id="upload-dept"
                value={dept}
                onChange={(e) => setDept(e.target.value)}
                className="border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>
        </section>
      )}

      {/* ── Drop zone ──────────────────────────────────────────────────── */}
      {!isActive && !isDone && (
        <section aria-label="File upload area">
          <div
            role="button"
            tabIndex={0}
            aria-label="Drop result file here or click to browse"
            className={`
              relative border-2 border-dashed rounded-lg p-10 text-center transition-colors cursor-pointer
              focus:outline-none focus:ring-2 focus:ring-blue-500
              ${dragOver
                ? 'border-blue-400 bg-blue-50'
                : fileError
                  ? 'border-red-300 bg-red-50'
                  : file
                    ? 'border-emerald-400 bg-emerald-50'
                    : 'border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50'
              }
            `}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_FILE_TYPES.join(',')}
              onChange={handleInputChange}
              className="sr-only"
              aria-hidden="true"
            />
            {file ? (
              <div className="flex flex-col items-center gap-2">
                <FileSpreadsheet size={36} className="text-emerald-500" aria-hidden="true" />
                <div className="text-sm font-semibold text-gray-800">{file.name}</div>
                <div className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
                <button
                  onClick={(e) => { e.stopPropagation(); handleRemoveFile(); }}
                  className="mt-1 inline-flex items-center gap-1 text-xs text-gray-500 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 rounded px-1"
                  aria-label="Remove selected file"
                >
                  <X size={12} /> Remove
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <UploadCloud size={40} className={`${dragOver ? 'text-blue-500' : 'text-gray-400'}`} aria-hidden="true" />
                <div className="text-sm font-medium text-gray-700">
                  {dragOver ? 'Drop file here' : 'Drag & drop or click to browse'}
                </div>
                <div className="text-xs text-gray-500">
                  Accepted: {ACCEPTED_FILE_TYPES.join(', ')} · Max {MAX_FILE_SIZE_MB} MB
                </div>
              </div>
            )}
          </div>

          {fileError && (
            <div className="mt-2 flex items-center gap-2 text-sm text-red-600" role="alert">
              <AlertCircle size={14} aria-hidden="true" />
              {fileError}
            </div>
          )}

          {file && !fileError && (
            <div className="mt-4">
              <button
                onClick={handleUpload}
                className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
              >
                <UploadCloud size={16} aria-hidden="true" />
                Upload &amp; Validate
              </button>
            </div>
          )}
        </section>
      )}

      {/* ── Pipeline progress ───────────────────────────────────────────── */}
      {isActive && (
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-sm p-6"
          aria-label="Upload pipeline progress"
          aria-live="polite"
        >
          <div className="flex items-center gap-3 mb-6">
            <Loader2 size={20} className="text-blue-500 animate-spin flex-shrink-0" aria-hidden="true" />
            <div>
              <div className="text-sm font-semibold text-gray-800">{message}</div>
              <div className="text-xs text-gray-500 mt-0.5">{file?.name}</div>
            </div>
          </div>

          {/* Step progress */}
          <ol className="flex flex-col gap-3" aria-label="Pipeline steps">
            {PIPELINE_STEPS.map((step, idx) => {
              const done    = idx < currentStep || isDone;
              const active  = idx === currentStep && !isDone;
              const pending = idx > currentStep;
              return (
                <li key={step.status} className="flex items-start gap-3">
                  <div
                    className={`
                      w-6 h-6 rounded-full flex-shrink-0 flex items-center justify-center mt-0.5 text-xs font-bold
                      ${done   ? 'bg-emerald-500 text-white'
                      : active ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                      :          'bg-gray-200 text-gray-400'}
                    `}
                    aria-label={done ? `${step.label} complete` : active ? `${step.label} in progress` : step.label}
                  >
                    {done ? <CheckCircle2 size={14} aria-hidden="true" /> : idx + 1}
                  </div>
                  <div className={`flex-1 ${pending ? 'opacity-40' : ''}`}>
                    <div className={`text-sm font-medium ${active ? 'text-blue-700' : done ? 'text-gray-700' : 'text-gray-500'}`}>
                      {step.label}
                    </div>
                    <div className="text-xs text-gray-500">{step.description}</div>
                  </div>
                  {active && (
                    <Loader2 size={14} className="text-blue-400 animate-spin flex-shrink-0 mt-1" aria-hidden="true" />
                  )}
                </li>
              );
            })}
          </ol>

          {/* Upload progress bar */}
          {status === 'UPLOADING' && percent > 0 && (
            <div className="mt-4">
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>Uploading…</span>
                <span>{percent}%</span>
              </div>
              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden" role="progressbar" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}>
                <div
                  className="h-full bg-blue-500 rounded-full transition-all duration-300"
                  style={{ width: `${percent}%` }}
                />
              </div>
            </div>
          )}
        </section>
      )}

      {/* ── Failed state ────────────────────────────────────────────────── */}
      {isFailed && (
        <section
          className="bg-red-50 border border-red-200 rounded-lg p-5"
          role="alert"
          aria-live="assertive"
        >
          <div className="flex items-start gap-3">
            <AlertCircle size={20} className="text-red-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-red-800">Upload failed</div>
              <div className="text-sm text-red-700 mt-0.5">{error}</div>
            </div>
          </div>
          <button
            onClick={handleReset}
            className="mt-4 inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium border border-red-300 text-red-700 bg-white rounded-md hover:bg-red-50 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            Try again
          </button>
        </section>
      )}

      {/* ── Completed / result ──────────────────────────────────────────── */}
      {isDone && result && (
        <div className="flex flex-col gap-4">
          {/* Success banner */}
          <section
            className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-start gap-3"
            role="status"
            aria-live="polite"
          >
            <CheckCircle2 size={20} className="text-emerald-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div className="flex-1">
              <div className="text-sm font-semibold text-emerald-800">Ingestion complete</div>
              <div className="text-xs text-emerald-700 mt-0.5">{result.fileName}</div>
            </div>
          </section>

          {/* Ingestion metrics */}
          <section
            className="bg-white rounded-lg border border-gray-200 shadow-sm p-4"
            aria-label="Ingestion summary"
          >
            <h2 className="text-sm font-semibold text-gray-800 mb-3">Ingestion Summary</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                { label: 'Records Received',  value: result.recordsReceived,  color: 'text-gray-800' },
                { label: 'Records Accepted',  value: result.recordsAccepted,  color: 'text-emerald-700' },
                { label: 'Records Rejected',  value: result.recordsRejected,  color: result.recordsRejected > 0 ? 'text-red-700' : 'text-gray-800' },
                { label: 'Students Identified', value: result.studentsIdentified, color: 'text-gray-800' },
                { label: 'Courses Identified',  value: result.coursesIdentified,  color: 'text-gray-800' },
                { label: 'Validation Issues', value: result.errorCount + result.warningCount, color: (result.errorCount + result.warningCount) > 0 ? 'text-amber-700' : 'text-emerald-700' },
              ].map((m) => (
                <div key={m.label} className="p-3 bg-gray-50 rounded-md border border-gray-100">
                  <div className="text-xs text-gray-500">{m.label}</div>
                  <div className={`text-lg font-semibold mt-0.5 ${m.color}`}>
                    {m.value.toLocaleString('en-IN')}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Validation issues */}
          {result.validationIssues.length > 0 && (
            <section
              className="bg-white rounded-lg border border-gray-200 shadow-sm p-4"
              aria-label="Validation issues"
            >
              <div className="flex items-center gap-3 mb-3 flex-wrap">
                <h2 className="text-sm font-semibold text-gray-800">Validation Issues</h2>
                {errors.length > 0 && (
                  <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
                    {errors.length} error{errors.length !== 1 ? 's' : ''}
                  </span>
                )}
                {warnings.length > 0 && (
                  <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
                    {warnings.length} warning{warnings.length !== 1 ? 's' : ''}
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-2">
                {result.validationIssues.map((issue, i) => (
                  <ValidationIssueRow key={i} issue={issue} />
                ))}
              </div>
              {errors.length > 0 && (
                <div className="mt-3 p-2.5 bg-red-50 border border-red-200 rounded text-xs text-red-700">
                  <strong>{result.recordsRejected}</strong> records were rejected due to the errors above
                  and are excluded from the analysis.
                </div>
              )}
            </section>
          )}

          {/* Actions */}
          <div className="flex items-center gap-3 flex-wrap">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
            >
              View Analysis →
            </Link>
            <Link
              to="/courses"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium border border-gray-200 text-gray-700 bg-white rounded-md hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
            >
              Course Analysis
            </Link>
            <button
              onClick={handleReset}
              className="text-sm text-gray-500 hover:text-gray-700 underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            >
              Upload another file
            </button>
          </div>
        </div>
      )}

      {/* ── Format guide ─────────────────────────────────────────────────── */}
      {!isActive && !isDone && (
        <section
          className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm"
          aria-label="File format requirements"
        >
          <h2 className="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-1.5">
            <Info size={14} aria-hidden="true" />
            Expected File Format
          </h2>
          <p className="text-xs text-blue-700 mb-2">
            The uploaded file should contain one row per student-course result with the following columns:
          </p>
          <ul className="grid grid-cols-2 sm:grid-cols-3 gap-x-4 gap-y-1 text-xs text-blue-800 font-mono">
            {['roll_number', 'student_name', 'course_code', 'course_name', 'internal_marks', 'external_marks', 'total_marks', 'grade', 'semester', 'academic_year'].map((col) => (
              <li key={col} className="flex items-center gap-1">
                <span className="w-1 h-1 rounded-full bg-blue-400 flex-shrink-0" aria-hidden="true" />
                {col}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
