import {
  AlertTriangle, BookOpen, Building2, CheckCircle2, Download,
  FileText, Loader2, Printer, TrendingUp, Trophy,
} from 'lucide-react';
import { useState } from 'react';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { useReportGenerator } from '@/hooks/useReports';
import type { ReportFormat, ReportRequest, ReportType } from '@/types/report';
import { ACADEMIC_YEARS, CURRENT_ACADEMIC_YEAR, CURRENT_DEPARTMENT, CURRENT_SEMESTER, DEPARTMENTS, REPORT_OPTIONS, SEMESTERS } from '@/utils/constants';

const REPORT_ICONS: Record<string, React.ReactNode> = {
  FileText:    <FileText size={20} aria-hidden="true" />,
  Building2:   <Building2 size={20} aria-hidden="true" />,
  BookOpen:    <BookOpen size={20} aria-hidden="true" />,
  Trophy:      <Trophy size={20} aria-hidden="true" />,
  AlertTriangle: <AlertTriangle size={20} aria-hidden="true" />,
  TrendingUp:  <TrendingUp size={20} aria-hidden="true" />,
};

const STATUS_STEPS = [
  { status: 'PREPARING',  label: 'Preparing',  description: 'Gathering required data' },
  { status: 'ANALYZING',  label: 'Analyzing',  description: 'Running analysis pipeline' },
  { status: 'GENERATING', label: 'Generating', description: 'Assembling report document' },
  { status: 'READY',      label: 'Ready',      description: 'Report is ready' },
];

export default function Reports() {
  const [selectedType, setSelectedType] = useState<ReportType | null>(null);
  const [year, setYear]   = useState(CURRENT_ACADEMIC_YEAR);
  const [sem, setSem]     = useState(CURRENT_SEMESTER);
  const [dept, setDept]   = useState(CURRENT_DEPARTMENT);
  const [format, setFormat] = useState<ReportFormat>('PDF');

  const { status, job, error, generate, download, reset } = useReportGenerator();

  const isGenerating = status === 'PREPARING' || status === 'ANALYZING' || status === 'GENERATING';
  const isReady      = status === 'READY';
  const isFailed     = status === 'FAILED';
  const isIdle       = status === 'IDLE';

  const selectedOption = REPORT_OPTIONS.find((o) => o.type === selectedType);

  async function handleGenerate() {
    if (!selectedType) return;
    const req: ReportRequest = {
      reportType: selectedType,
      academicYear: year,
      semester: sem,
      department: dept,
      format,
    };
    await generate(req);
  }

  function handleDownload() {
    if (job?.jobId) download(job.jobId);
  }

  const currentStepIdx = STATUS_STEPS.findIndex((s) => s.status === status);

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <PageHeader
        title="Reports"
        description="Generate and download institutional result analysis reports."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Reports' }]}
      />

      {/* Report type selection */}
      {isIdle && (
        <section aria-label="Report type selection">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Select Report Type</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {REPORT_OPTIONS.map((option) => (
              <button
                key={option.type}
                onClick={() => setSelectedType(option.type)}
                className={`
                  flex items-start gap-3 p-4 rounded-lg border text-left transition-all
                  focus:outline-none focus:ring-2 focus:ring-blue-500
                  ${selectedType === option.type
                    ? 'border-blue-500 bg-blue-50 shadow-sm'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
                  }
                `}
                aria-pressed={selectedType === option.type}
              >
                <span className={`flex-shrink-0 mt-0.5 ${selectedType === option.type ? 'text-blue-600' : 'text-gray-400'}`}>
                  {REPORT_ICONS[option.icon]}
                </span>
                <div>
                  <div className="text-sm font-medium text-gray-900">{option.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5 leading-snug">{option.description}</div>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Report parameters */}
      {isIdle && selectedType && (
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-sm p-5"
          aria-label="Report parameters"
        >
          <h2 className="text-sm font-semibold text-gray-800 mb-4">
            Configure — {selectedOption?.label}
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-5">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide" htmlFor="rep-year">Academic Year</label>
              <select id="rep-year" value={year} onChange={(e) => setYear(e.target.value)}
                className="border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {ACADEMIC_YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide" htmlFor="rep-sem">Semester</label>
              <select id="rep-sem" value={sem} onChange={(e) => setSem(Number(e.target.value))}
                className="border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                {SEMESTERS.map((s) => <option key={s} value={s}>Semester {s}</option>)}
              </select>
            </div>
            {selectedOption?.requiresDepartment && (
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-500 uppercase tracking-wide" htmlFor="rep-dept">Department</label>
                <select id="rep-dept" value={dept} onChange={(e) => setDept(e.target.value)}
                  className="border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                  {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            )}
          </div>

          {/* Format selector */}
          <div className="flex flex-col gap-1 mb-5">
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Output Format</label>
            <div className="flex gap-2">
              {(['PDF', 'EXCEL'] as ReportFormat[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`px-3 py-1.5 text-sm rounded-md border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    format === f ? 'border-blue-500 bg-blue-50 text-blue-700 font-medium' : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                  }`}
                  aria-pressed={format === f}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleGenerate}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
            >
              <FileText size={15} aria-hidden="true" />
              Generate Report
            </button>
            <button
              onClick={() => setSelectedType(null)}
              className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancel
            </button>
          </div>
        </section>
      )}

      {/* No selection */}
      {isIdle && !selectedType && (
        <EmptyState
          title="Select a report type above"
          description="Choose the type of report you need, configure the parameters, and generate."
          icon={<FileText size={40} strokeWidth={1.5} />}
          className="py-8"
        />
      )}

      {/* Generation progress */}
      {isGenerating && (
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-sm p-6"
          aria-live="polite"
          aria-label="Report generation progress"
        >
          <div className="flex items-center gap-3 mb-6">
            <Loader2 size={20} className="text-blue-500 animate-spin" aria-hidden="true" />
            <div>
              <div className="text-sm font-semibold text-gray-800">Generating report…</div>
              <div className="text-xs text-gray-500">{selectedOption?.label} · {year} Sem {sem}</div>
            </div>
          </div>

          <ol className="flex flex-col gap-3" aria-label="Generation steps">
            {STATUS_STEPS.map((step, idx) => {
              const done    = idx < currentStepIdx;
              const active  = idx === currentStepIdx;
              const pending = idx > currentStepIdx;
              return (
                <li key={step.status} className="flex items-start gap-3">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold mt-0.5 ${
                    done   ? 'bg-emerald-500 text-white'
                    : active ? 'bg-blue-600 text-white ring-4 ring-blue-100'
                    :          'bg-gray-200 text-gray-400'
                  }`}>
                    {done ? <CheckCircle2 size={14} aria-hidden="true" /> : idx + 1}
                  </div>
                  <div className={pending ? 'opacity-40' : ''}>
                    <div className={`text-sm font-medium ${active ? 'text-blue-700' : done ? 'text-gray-700' : 'text-gray-500'}`}>{step.label}</div>
                    <div className="text-xs text-gray-500">{step.description}</div>
                  </div>
                  {active && <Loader2 size={14} className="text-blue-400 animate-spin flex-shrink-0 mt-1 ml-auto" aria-hidden="true" />}
                </li>
              );
            })}
          </ol>
        </section>
      )}

      {/* Ready state */}
      {isReady && job && (
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-sm p-6"
          aria-live="polite"
          aria-label="Report ready"
        >
          <div className="flex items-center gap-3 mb-5">
            <CheckCircle2 size={22} className="text-emerald-500" aria-hidden="true" />
            <div>
              <div className="text-sm font-semibold text-gray-800">Report ready</div>
              <div className="text-xs text-gray-500 font-mono mt-0.5">{job.fileName}</div>
            </div>
          </div>

          <div className="flex gap-3 flex-wrap">
            <button
              onClick={handleDownload}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
            >
              <Download size={15} aria-hidden="true" />
              Download {format}
            </button>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 px-4 py-2 border border-gray-200 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <Printer size={15} aria-hidden="true" />
              Print
            </button>
            <button
              onClick={reset}
              className="text-sm text-gray-500 hover:text-gray-700 underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded ml-2"
            >
              Generate another
            </button>
          </div>

          {job.downloadUrl === null && (
            <p className="mt-4 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              Demo mode: Download is unavailable. In production, this button will download the generated PDF from the backend.
            </p>
          )}
        </section>
      )}

      {/* Error state */}
      {isFailed && (
        <ErrorState
          message={error ?? 'Report generation failed. Please try again.'}
          onRetry={reset}
          className="py-12"
        />
      )}
    </div>
  );
}
