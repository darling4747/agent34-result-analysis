import { AlertCircle, BookOpen, CheckCircle2, Loader2, Sparkles, TriangleAlert } from 'lucide-react';
import { useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { useDataset } from '@/hooks/useDataset';
import { useDatasetContext } from '@/contexts/DatasetContext';
import { generateAutoNarrative } from '@/api/analysisApi';
import { ApiError } from '@/api/client';
import type { AnalyticalNarrative } from '@/types/analysis';

export default function AIInsights() {
  const { refreshKey } = useDatasetContext();
  const { datasetInfo } = useDataset(refreshKey);
  const [narrative, setNarrative] = useState<AnalyticalNarrative | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!datasetInfo?.has_data) return;
    setLoading(true);
    setError(null);
    try {
      const res = await generateAutoNarrative({
        academicYear: datasetInfo.academic_year ?? undefined,
        semester: datasetInfo.semester ?? undefined,
        department: datasetInfo.department ?? undefined,
      });
      setNarrative(res.data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to generate insights.');
    } finally {
      setLoading(false);
    }
  }

  const modelUsed = narrative?.model_used ?? narrative?.model ?? '';
  const keyFindings = narrative?.key_findings ?? narrative?.keyFindings ?? [];
  const recommendations = narrative?.recommendations ?? [];

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      <PageHeader
        title="AI Insights"
        description="Gemini-powered analytical narrative generated from verified institutional metrics."
        breadcrumbs={[{ label: 'Overview', to: '/dashboard' }, { label: 'AI Insights' }]}
        actions={
          <button
            onClick={handleGenerate}
            disabled={loading || !datasetInfo?.has_data}
            className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            {loading ? <Loader2 size={15} className="animate-spin" /> : <Sparkles size={15} />}
            {loading ? 'Generating…' : narrative ? 'Regenerate' : 'Generate Insights'}
          </button>
        }
      />

      {/* Architecture note */}
      <div className="flex items-start gap-2.5 bg-purple-50 border border-purple-200 rounded-md px-4 py-3">
        <Sparkles size={14} className="text-purple-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <p className="text-xs text-purple-800">
          <strong>How this works:</strong> Agent 34 computes all numerical metrics (pass rate, GPA, correlation, etc.)
          using Pandas/NumPy/SciPy. Only the verified metrics are sent to Gemini for narrative generation.
          Gemini cannot modify any numbers.
        </p>
      </div>

      {!datasetInfo?.has_data && (
        <EmptyState
          title="No dataset available"
          description="Upload a result dataset first to generate AI insights."
          icon={<BookOpen size={40} strokeWidth={1.5} />}
        />
      )}

      {error && (
        <ErrorState message={error} onRetry={handleGenerate} />
      )}

      {!loading && !narrative && datasetInfo?.has_data && !error && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-10 text-center">
          <Sparkles size={40} className="text-purple-300 mx-auto mb-3" />
          <p className="text-sm text-gray-600">Click <strong>Generate Insights</strong> to create an AI-powered narrative from your current dataset.</p>
        </div>
      )}

      {loading && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-10 text-center">
          <Loader2 size={40} className="text-purple-400 animate-spin mx-auto mb-3" />
          <p className="text-sm text-gray-600">Generating insights… Gemini is analysing your verified metrics.</p>
        </div>
      )}

      {narrative && !loading && (
        <>
          {/* Model badge */}
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-purple-100 text-purple-800 border border-purple-200 rounded-full text-xs font-medium">
              <Sparkles size={11} aria-hidden="true" />
              {modelUsed.startsWith('gemini') ? 'Gemini AI' : modelUsed === 'deterministic' ? 'Deterministic Engine' : modelUsed || 'Gemini AI'}
            </span>
            <span className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-2 py-0.5">
              AI-generated draft — Human review required
            </span>
          </div>

          {/* Summary */}
          <section className="bg-white rounded-lg border border-gray-200 shadow-sm p-5" aria-label="Summary">
            <h2 className="text-sm font-semibold text-gray-800 mb-2">Summary</h2>
            <p className="text-sm text-gray-700 leading-relaxed">{narrative.summary}</p>
          </section>

          {/* Key Findings */}
          {keyFindings.length > 0 && (
            <section className="bg-white rounded-lg border border-gray-200 shadow-sm p-5" aria-label="Key findings">
              <h2 className="text-sm font-semibold text-gray-800 mb-3">Key Findings</h2>
              <ul className="flex flex-col gap-2" role="list">
                {keyFindings.map((f: string, i: number) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-gray-700">
                    <CheckCircle2 size={14} className="text-blue-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    {f}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <section className="bg-white rounded-lg border border-gray-200 shadow-sm p-5" aria-label="Recommendations">
              <h2 className="text-sm font-semibold text-gray-800 mb-3">Recommendations</h2>
              <ul className="flex flex-col gap-2" role="list">
                {recommendations.map((r: string, i: number) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-gray-700">
                    <TriangleAlert size={14} className="text-amber-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
                    {r}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {/* Disclaimer */}
          {narrative.disclaimer && (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-md text-xs text-gray-600 flex items-start gap-2">
              <AlertCircle size={13} className="flex-shrink-0 mt-0.5 text-gray-400" aria-hidden="true" />
              {narrative.disclaimer}
            </div>
          )}
        </>
      )}
    </div>
  );
}
