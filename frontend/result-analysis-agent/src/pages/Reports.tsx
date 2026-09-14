import {
  AlertTriangle, BookOpen, Building2, CheckCircle2, Download,
  FileText, Loader2, Printer, TrendingUp, Trophy, Clock, RefreshCw,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { useReportGenerator } from '@/hooks/useReports';
import { getReportJobs } from '@/api/reportsApi';
import type { ReportFormat, ReportJob, ReportRequest, ReportType } from '@/types/report';
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
  const [recentJobs, setRecentJobs] = useState<ReportJob[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);

  const { status, job, error, generate, download, reset } = useReportGenerator();

  const isGenerating = status === 'PREPARING' || status === 'ANALYZING' || status === 'GENERATING';
  const isReady      = status === 'READY';
  const isFailed     = status === 'FAILED';
  const isIdle       = status === 'IDLE';

  const selectedOption = REPORT_OPTIONS.find((o) => o.type === selectedType);

  const fetchRecentJobs = async () => {
    try {
      setLoadingJobs(true);
      const jobs = await getReportJobs();
      setRecentJobs(jobs);
    } catch {
      // Graceful fallback if backend has no jobs history
    } finally {
      setLoadingJobs(false);
    }
  };

  useEffect(() => {
    fetchRecentJobs();
  }, [status]);

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

  function handleDownload(targetJobId?: string, targetFileName?: string) {
    const id = targetJobId || job?.jobId;
    const name = targetFileName || job?.fileName || undefined;
    if (id) download(id, name);
  }

  const currentStepIdx = STATUS_STEPS.findIndex((s) => s.status === status);

  return (
    <div className="flex flex-col gap-6 max-w-5xl">
      <PageHeader
        title="Report Center"
        description="Institutional Intelligence & Decision Support — Generate and download official academic analysis reports."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'Report Center' }]}
      />

      {/* Active Dataset Context Bar */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-900 text-white rounded-lg p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="text-xs uppercase tracking-wider text-blue-200 font-semibold">Active Dataset Scope</div>
          <div className="text-base font-bold mt-0.5">Academic Year {year} — Semester {sem}</div>
        </div>
        <div className="flex items-center gap-4 text-xs text-blue-100">
          <div><span className="font-semibold text-white">Department:</span> {dept}</div>
          <div><span className="font-semibold text-white">Status:</span> Authenticated Session</div>
        </div>
      </div>

      {/* Report type selection */}
      {isIdle && (
        <section aria-label="Report type selection">
          <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">Select Report Type</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {REPORT_OPTIONS.map((option) => (
              <button
                key={option.type}
                onClick={() => setSelectedType(option.type)}
                className={`
                  flex items-start gap-3 p-4 rounded-lg border text-left transition-all
                  focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer
                  ${selectedType === option.type
                    ? 'border-blue-600 bg-blue-50/80 shadow-md ring-1 ring-blue-500'
                    : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50/60 shadow-sm'
                  }
                `}
                aria-pressed={selectedType === option.type}
              >
                <span className={`flex-shrink-0 mt-0.5 p-2 rounded-md ${selectedType === option.type ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600'}`}>
                  {REPORT_ICONS[option.icon]}
                </span>
                <div>
                  <div className="text-sm font-semibold text-gray-900">{option.label}</div>
                  <div className="text-xs text-gray-500 mt-1 leading-snug">{option.description}</div>
                </div>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Report parameters */}
      {isIdle && selectedType && (
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-md p-6"
          aria-label="Report parameters"
        >
          <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-5">
            <h2 className="text-base font-semibold text-gray-800">
              Configure Report — <span className="text-blue-600">{selectedOption?.label}</span>
            </h2>
            <span className="text-xs font-mono text-gray-400">FORMAT: {format}</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-5">
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-600 uppercase tracking-wide" htmlFor="rep-year">Academic Year</label>
              <select id="rep-year" value={year} onChange={(e) => setYear(e.target.value)}
                className="border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                {ACADEMIC_YEARS.map((y) => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-600 uppercase tracking-wide" htmlFor="rep-sem">Semester</label>
              <select id="rep-sem" value={sem} onChange={(e) => setSem(Number(e.target.value))}
                className="border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                {SEMESTERS.map((s) => <option key={s} value={s}>Semester {s}</option>)}
              </select>
            </div>
            {selectedOption?.requiresDepartment && (
              <div className="flex flex-col gap-1">
                <label className="text-xs font-medium text-gray-600 uppercase tracking-wide" htmlFor="rep-dept">Department</label>
                <select id="rep-dept" value={dept} onChange={(e) => setDept(e.target.value)}
                  className="border border-gray-200 rounded-md px-3 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                  {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
                </select>
              </div>
            )}
          </div>

          {/* Format selector */}
          <div className="flex flex-col gap-1.5 mb-6">
            <label className="text-xs font-medium text-gray-600 uppercase tracking-wide">Output Format</label>
            <div className="flex gap-2">
              {(['PDF', 'EXCEL'] as ReportFormat[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFormat(f)}
                  className={`px-4 py-1.5 text-xs font-semibold rounded-md border transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    format === f ? 'border-blue-600 bg-blue-600 text-white' : 'border-gray-200 text-gray-700 bg-white hover:bg-gray-50'
                  }`}
                  aria-pressed={format === f}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-2 border-t border-gray-100">
            <button
              onClick={handleGenerate}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <FileText size={16} aria-hidden="true" />
              Generate Report
            </button>
            <button
              onClick={() => setSelectedType(null)}
              className="px-4 py-2.5 text-sm text-gray-600 border border-gray-200 rounded-md hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          description="Choose from one of the six institutional report options to configure parameters and generate output."
          icon={<FileText size={40} strokeWidth={1.5} />}
          className="py-8 bg-white border border-gray-100 rounded-lg shadow-sm"
        />
      )}

      {/* Generation progress */}
      {isGenerating && (
        <section
          className="bg-white rounded-lg border border-gray-200 shadow-md p-6"
          aria-live="polite"
          aria-label="Report generation progress"
        >
          <div className="flex items-center gap-3 mb-6">
            <Loader2 size={24} className="text-blue-600 animate-spin" aria-hidden="true" />
            <div>
              <div className="text-base font-semibold text-gray-800">Generating Report…</div>
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
          className="bg-white rounded-lg border border-gray-200 shadow-md p-6"
          aria-live="polite"
          aria-label="Report ready"
        >
          <div className="flex items-center gap-3 mb-5">
            <CheckCircle2 size={26} className="text-emerald-600" aria-hidden="true" />
            <div>
              <div className="text-base font-bold text-gray-900">REPORT READY</div>
              <div className="text-xs text-gray-500 font-mono mt-0.5">{job.fileName || `report_${job.jobId}.pdf`}</div>
            </div>
          </div>

          <div className="flex gap-3 flex-wrap items-center">
            <button
              onClick={() => handleDownload()}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <Download size={16} aria-hidden="true" />
              Download Report ({format})
            </button>
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 px-4 py-2.5 border border-gray-200 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <Printer size={16} aria-hidden="true" />
              Print
            </button>
            <button
              onClick={reset}
              className="text-sm text-gray-600 hover:text-gray-900 underline focus:outline-none focus:ring-2 focus:ring-blue-500 rounded ml-2"
            >
              Generate Another
            </button>
          </div>
        </section>
      )}

      {/* Error state */}
      {isFailed && (
        <ErrorState
          message={error ?? 'Report generation failed. Please try again.'}
          onRetry={reset}
          className="py-8"
        />
      )}

      {/* Recent Reports Table */}
      <section className="bg-white rounded-lg border border-gray-200 shadow-sm p-5 mt-2">
        <div className="flex items-center justify-between border-b border-gray-100 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Clock size={16} className="text-gray-500" />
            <h2 className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Recent Reports</h2>
          </div>
          <button
            onClick={fetchRecentJobs}
            disabled={loadingJobs}
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1 focus:outline-none"
          >
            <RefreshCw size={12} className={loadingJobs ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {recentJobs.length === 0 ? (
          <div className="text-xs text-gray-500 py-4 text-center">No recent report history found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-gray-700">
              <thead className="bg-gray-50 text-gray-500 uppercase tracking-wider font-semibold border-b border-gray-200">
                <tr>
                  <th className="px-3 py-2">Report ID</th>
                  <th className="px-3 py-2">Type</th>
                  <th className="px-3 py-2">Academic Year</th>
                  <th className="px-3 py-2">Sem</th>
                  <th className="px-3 py-2">Format</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 font-mono">
                {recentJobs.map((r) => (
                  <tr key={r.jobId} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-semibold text-gray-900">#{r.jobId}</td>
                    <td className="px-3 py-2 font-sans font-medium">{r.reportType}</td>
                    <td className="px-3 py-2">{r.parameters.academicYear || '—'}</td>
                    <td className="px-3 py-2">Sem {r.parameters.semester}</td>
                    <td className="px-3 py-2">{r.parameters.format}</td>
                    <td className="px-3 py-2 font-sans">
                      <span className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                        r.status === 'READY' ? 'bg-emerald-100 text-emerald-800'
                        : r.status === 'FAILED' ? 'bg-red-100 text-red-800'
                        : 'bg-blue-100 text-blue-800'
                      }`}>
                        {r.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-sans">
                      {r.status === 'READY' ? (
                        <button
                          onClick={() => handleDownload(r.jobId, r.fileName || undefined)}
                          className="text-blue-600 hover:text-blue-800 font-medium text-xs flex items-center gap-1 focus:outline-none"
                        >
                          <Download size={12} /> Download
                        </button>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
