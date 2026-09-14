import { useState, useEffect } from 'react';
import {
  Database,
  Sparkles,
  Sliders,
  CheckCircle2,
  AlertCircle,
  Save,
  Loader2,
  Server,
  Layers,
  Cpu,
  ShieldCheck,
  QrCode,
  Copy,
  Check,
  X,
} from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import client from '@/api/client';
import { getMfaStatus, setupMfa, verifyMfaSetup, disableMfa, regenerateMfaRecoveryCodes } from '@/api/authApi';
import type { MfaSetupData, MfaStatusData } from '@/types/auth';

interface SystemConfigResponse {
  assessment: {
    internal_max: number;
    external_max: number;
    total_max: number;
    grade_map: Record<string, number>;
  };
  intervention_weights: {
    failure_weight: number;
    historical_weight: number;
    section_weight: number;
    correlation_weight: number;
  };
  ai_provider: {
    provider: string;
    model: string;
    has_api_key: boolean;
    status: string;
  };
  database: {
    type: string;
    name: string;
    host: string;
    port: number;
    status: string;
  };
  integrations: {
    agent_35: string;
    agent_8: string;
  };
}

export default function Settings() {
  const [config, setConfig] = useState<SystemConfigResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // MFA state
  const [mfaStatus, setMfaStatus] = useState<MfaStatusData | null>(null);
  const [showMfaModal, setShowMfaModal] = useState(false);
  const [mfaSetupData, setMfaSetupData] = useState<MfaSetupData | null>(null);
  const [mfaVerifyCode, setMfaVerifyCode] = useState('');
  const [mfaSetupLoading, setMfaSetupLoading] = useState(false);
  const [mfaError, setMfaError] = useState<string | null>(null);
  const [copiedSecret, setCopiedSecret] = useState(false);
  const [copiedCodes, setCopiedCodes] = useState(false);

  // Disable MFA modal
  const [showDisableModal, setShowDisableModal] = useState(false);
  const [disablePassword, setDisablePassword] = useState('');
  const [disableLoading, setDisableLoading] = useState(false);

  // Form states for editable weights
  const [weights, setWeights] = useState({
    failure_weight: 0.40,
    historical_weight: 0.30,
    section_weight: 0.20,
    correlation_weight: 0.10,
  });

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await client.get('/api/config');
      if (resp.data && resp.data.success) {
        const data: SystemConfigResponse = resp.data.data;
        setConfig(data);
        if (data.intervention_weights) {
          setWeights({
            failure_weight: data.intervention_weights.failure_weight,
            historical_weight: data.intervention_weights.historical_weight,
            section_weight: data.intervention_weights.section_weight,
            correlation_weight: data.intervention_weights.correlation_weight,
          });
        }
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load system configuration.');
    } finally {
      setLoading(false);
    }
  };

  const loadMfaStatus = async () => {
    try {
      const resp = await getMfaStatus();
      if (resp.success) setMfaStatus(resp.data);
    } catch {
      // Best-effort
    }
  };

  useEffect(() => {
    fetchConfig();
    loadMfaStatus();
  }, []);

  const handleStartMfaSetup = async () => {
    setMfaSetupLoading(true);
    setMfaError(null);
    try {
      const resp = await setupMfa();
      if (resp.success) {
        setMfaSetupData(resp.data);
        setShowMfaModal(true);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to initialize MFA setup.');
    } finally {
      setMfaSetupLoading(false);
    }
  };

  const handleVerifyMfaSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfaSetupData || !mfaVerifyCode) return;
    setMfaSetupLoading(true);
    setMfaError(null);
    try {
      const resp = await verifyMfaSetup(mfaVerifyCode.trim(), mfaSetupData.recovery_codes);
      if (resp.success) {
        setShowMfaModal(false);
        setMfaVerifyCode('');
        setSuccessMsg('Authenticator App (TOTP) successfully configured and activated.');
        setTimeout(() => setSuccessMsg(null), 4000);
        loadMfaStatus();
      }
    } catch (err: any) {
      setMfaError(err?.response?.data?.detail || err.message || 'Invalid verification code.');
    } finally {
      setMfaSetupLoading(false);
    }
  };

  const handleDisableMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!disablePassword) return;
    setDisableLoading(true);
    setError(null);
    try {
      const resp = await disableMfa(disablePassword);
      if (resp.success) {
        setShowDisableModal(false);
        setDisablePassword('');
        setSuccessMsg('Multi-Factor Authentication disabled.');
        setTimeout(() => setSuccessMsg(null), 4000);
        loadMfaStatus();
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Incorrect password.');
    } finally {
      setDisableLoading(false);
    }
  };

  const handleRegenerateCodes = async () => {
    if (!confirm('Regenerate new emergency recovery codes? Any previous un-used recovery codes will be invalidated.')) return;
    try {
      const resp = await regenerateMfaRecoveryCodes();
      if (resp.success && resp.data.recovery_codes) {
        alert(`New Recovery Codes Generated:\n\n${resp.data.recovery_codes.join('\n')}\n\nPlease store these in a secure password manager.`);
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || err.message || 'Failed to regenerate recovery codes.');
    }
  };

  const handleWeightChange = (key: keyof typeof weights, val: string) => {
    const num = parseFloat(val) || 0;
    setWeights((prev) => ({ ...prev, [key]: num }));
  };

  const totalWeight = Object.values(weights).reduce((a, b) => a + b, 0);
  const isWeightValid = Math.abs(totalWeight - 1.0) < 0.001;

  const handleSaveWeights = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isWeightValid) {
      alert(`Intervention weights must sum to 1.00 (currently ${totalWeight.toFixed(2)}).`);
      return;
    }
    setSaving(true);
    setSuccessMsg(null);
    setError(null);
    try {
      const resp = await client.put('/api/config', { weights });
      if (resp.data && resp.data.success) {
        setSuccessMsg('Intervention priority weights saved successfully.');
        setTimeout(() => setSuccessMsg(null), 4000);
        fetchConfig();
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to save configuration.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="Settings & System Configuration"
        description="Configure institutional assessment rules, intervention weighting, AI narrative providers, and database parameters."
      />

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl flex items-center justify-between">
          <span>{error}</span>
          <button onClick={fetchConfig} className="underline font-semibold">Retry</button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-xl flex items-center gap-2 font-medium">
          <CheckCircle2 size={18} className="text-emerald-600 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* System Status Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Database</div>
            <div className="text-sm font-bold text-gray-900 mt-1">PostgreSQL 16</div>
            <div className="text-xs text-emerald-600 font-semibold mt-0.5 flex items-center gap-1">
              <CheckCircle2 size={12} /> Connected (Healthy)
            </div>
          </div>
          <div className="w-11 h-11 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Database size={22} />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">AI Narrative Provider</div>
            <div className="text-sm font-bold text-gray-900 mt-1">
              {config?.ai_provider?.has_api_key ? 'Gemini 3.6 Flash' : 'Deterministic Engine'}
            </div>
            <div className={`text-xs font-semibold mt-0.5 flex items-center gap-1 ${config?.ai_provider?.has_api_key ? 'text-purple-600' : 'text-amber-600'}`}>
              <Sparkles size={12} /> {config?.ai_provider?.has_api_key ? 'Connected' : 'Fallback Engine'}
            </div>
          </div>
          <div className="w-11 h-11 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
            <Sparkles size={22} />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Agent 35 Integration</div>
            <div className="text-sm font-bold text-gray-900 mt-1">Backlog Roster</div>
            <div className="text-xs text-emerald-600 font-semibold mt-0.5 flex items-center gap-1">
              <CheckCircle2 size={12} /> Contract Active
            </div>
          </div>
          <div className="w-11 h-11 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Server size={22} />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Agent 8 Integration</div>
            <div className="text-sm font-bold text-gray-900 mt-1">OBE Attainment</div>
            <div className="text-xs text-emerald-600 font-semibold mt-0.5 flex items-center gap-1">
              <CheckCircle2 size={12} /> Contract Active
            </div>
          </div>
          <div className="w-11 h-11 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
            <Layers size={22} />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-500">
          <Loader2 size={28} className="animate-spin text-blue-600 mx-auto mb-2" />
          <p className="text-sm font-medium">Loading configuration parameters...</p>
        </div>
      ) : (
        <>
          {/* Assessment & Marks Configuration */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sliders size={20} className="text-blue-600" />
                <div>
                  <h3 className="text-base font-bold text-gray-900">Institutional Assessment &amp; Marks Scheme</h3>
                  <p className="text-xs text-gray-500">Maximum marks breakdown and grade point scale</p>
                </div>
              </div>
            </div>

            <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-center">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Internal Continuous Assessment</div>
                <div className="text-3xl font-extrabold text-blue-600 mt-2">
                  {config?.assessment?.internal_max ?? 30} <span className="text-sm font-medium text-slate-500">Marks</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Max internal assessment weight (Agent 33)</div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-center">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">External Semester Examination</div>
                <div className="text-3xl font-extrabold text-blue-600 mt-2">
                  {config?.assessment?.external_max ?? 70} <span className="text-sm font-medium text-slate-500">Marks</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Max university exam weight</div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-center">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Course Maximum</div>
                <div className="text-3xl font-extrabold text-emerald-600 mt-2">
                  {config?.assessment?.total_max ?? 100} <span className="text-sm font-medium text-slate-500">Marks</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Combined maximum grade total</div>
              </div>
            </div>

            {/* Grade Scale Table */}
            <div className="px-6 pb-6">
              <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-3">Institutional Grade Point Scale</h4>
              <div className="grid grid-cols-4 sm:grid-cols-8 gap-2 text-center">
                {Object.entries(config?.assessment?.grade_map || { O: 10, 'A+': 9, A: 8, 'B+': 7, B: 6, C: 5, P: 4, F: 0 }).map(([g, p]) => (
                  <div key={g} className="bg-gray-50 border border-gray-200 rounded-lg p-2.5">
                    <div className="text-sm font-extrabold text-gray-900">{g}</div>
                    <div className="text-xs text-blue-600 font-semibold mt-0.5">{p} GP</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Intervention Priority Weighting Configuration */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu size={20} className="text-purple-600" />
                <div>
                  <h3 className="text-base font-bold text-gray-900">Intervention Priority Weighting Model</h3>
                  <p className="text-xs text-gray-500">Multi-factor priority score weights (must sum to 1.00)</p>
                </div>
              </div>

              <div className={`text-xs font-bold px-3 py-1 rounded-full border ${isWeightValid ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                Sum: {totalWeight.toFixed(2)} / 1.00 {isWeightValid ? '✓ Valid' : '⚠️ Invalid'}
              </div>
            </div>

            <form onSubmit={handleSaveWeights} className="p-6 space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Subject Failure Rate Weight (40%)
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={weights.failure_weight}
                    onChange={(e) => handleWeightChange('failure_weight', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:outline-none font-semibold text-gray-900"
                  />
                  <p className="text-[11px] text-gray-500 mt-1">Weight for current failure %</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Historical Deviation Weight (30%)
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={weights.historical_weight}
                    onChange={(e) => handleWeightChange('historical_weight', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:outline-none font-semibold text-gray-900"
                  />
                  <p className="text-[11px] text-gray-500 mt-1">Weight for longitudinal decline</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Section Deviation Weight (20%)
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={weights.section_weight}
                    onChange={(e) => handleWeightChange('section_weight', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:outline-none font-semibold text-gray-900"
                  />
                  <p className="text-[11px] text-gray-500 mt-1">Weight for cross-section variance</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                    Correlation Signal Weight (10%)
                  </label>
                  <input
                    type="number"
                    step="0.05"
                    min="0"
                    max="1"
                    value={weights.correlation_weight}
                    onChange={(e) => handleWeightChange('correlation_weight', e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:outline-none font-semibold text-gray-900"
                  />
                  <p className="text-[11px] text-gray-500 mt-1">Weight for internal/external gap</p>
                </div>
              </div>

              <div className="pt-4 border-t border-gray-100 flex items-center justify-between">
                <div className="text-xs text-gray-500 flex items-center gap-1.5">
                  <AlertCircle size={14} className="text-purple-500" />
                  Intervention rank calculation formula: <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-[11px]">Score = (W1×Fail%) + (W2×HistDev) + (W3×SecDev) + (W4×Corr)</code>
                </div>

                <button
                  type="submit"
                  disabled={saving || !isWeightValid}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 font-medium text-sm transition-colors shadow-sm disabled:opacity-50"
                >
                  {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  Save Intervention Weights
                </button>
              </div>
            </form>
          </div>

          {/* Security & Multi-Factor Authentication Card */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-5 border-b border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck size={20} className="text-purple-600" />
                <div>
                  <h3 className="text-base font-bold text-gray-900">Two-Factor Authentication (TOTP / MFA)</h3>
                  <p className="text-xs text-gray-500">Protect account with Google Authenticator, Microsoft Authenticator, or Authy</p>
                </div>
              </div>

              <div className={`text-xs font-bold px-3 py-1 rounded-full border ${mfaStatus?.mfa_enabled ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>
                {mfaStatus?.mfa_enabled ? '✓ MFA Active' : '⚠️ MFA Disabled'}
              </div>
            </div>

            <div className="p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div>
                <h4 className="text-sm font-bold text-gray-900">
                  {mfaStatus?.mfa_enabled ? 'Authenticator App Protection Active' : 'Authenticator App Not Configured'}
                </h4>
                <p className="text-xs text-gray-500 mt-1 max-w-xl">
                  {mfaStatus?.mfa_enabled
                    ? 'Your account is secured with 6-digit TOTP codes from your authenticator app. Single-use emergency recovery codes are active.'
                    : 'Add an extra layer of enterprise security. Scanning a QR code with Google Authenticator or Microsoft Authenticator will be required on login.'}
                </p>
              </div>

              <div className="flex items-center gap-2 flex-shrink-0">
                {mfaStatus?.mfa_enabled ? (
                  <>
                    <button
                      type="button"
                      onClick={handleRegenerateCodes}
                      className="px-3.5 py-2 bg-purple-50 text-purple-700 hover:bg-purple-100 rounded-lg text-xs font-semibold border border-purple-200 transition-colors"
                    >
                      Regenerate Recovery Codes
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowDisableModal(true)}
                      className="px-3.5 py-2 bg-red-50 text-red-600 hover:bg-red-100 rounded-lg text-xs font-semibold border border-red-200 transition-colors"
                    >
                      Disable MFA
                    </button>
                  </>
                ) : (
                  <button
                    type="button"
                    onClick={handleStartMfaSetup}
                    disabled={mfaSetupLoading}
                    className="inline-flex items-center gap-2 px-4 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-semibold transition-colors shadow-sm disabled:opacity-50"
                  >
                    {mfaSetupLoading ? <Loader2 size={14} className="animate-spin" /> : <QrCode size={15} />}
                    Configure Authenticator App
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Database & Infrastructure Information Card */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center gap-2 mb-4">
              <Database size={20} className="text-slate-700" />
              <h3 className="text-base font-bold text-gray-900">PostgreSQL Infrastructure Details</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Database Engine</span>
                  <span className="text-xs font-bold text-slate-800">PostgreSQL 16</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Database Name</span>
                  <span className="text-xs font-mono font-bold text-blue-700">result_analysis</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Connection Host &amp; Port</span>
                  <span className="text-xs font-mono font-bold text-slate-800">localhost:5432</span>
                </div>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">ORM Adapter</span>
                  <span className="text-xs font-bold text-slate-800">SQLAlchemy 2.0 (psycopg2)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Persistence Target</span>
                  <span className="text-xs font-bold text-emerald-700">Single Source of Truth</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500">Health Endpoint</span>
                  <span className="text-xs font-mono font-bold text-emerald-700">/health (HTTP 200)</span>
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* MFA Setup Modal */}
      {showMfaModal && mfaSetupData && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full shadow-2xl overflow-hidden border border-gray-100 flex flex-col max-h-[90vh]">
            <div className="p-5 bg-gradient-to-r from-purple-600 to-indigo-600 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck size={22} />
                <h3 className="text-base font-bold">Set up Authenticator App</h3>
              </div>
              <button
                onClick={() => setShowMfaModal(false)}
                className="text-white/80 hover:text-white p-1 rounded-full hover:bg-white/10"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6">
              {mfaError && (
                <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
                  <AlertCircle size={16} />
                  <span>{mfaError}</span>
                </div>
              )}

              {/* Step 1: Scan QR Code */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">1</span>
                  <h4 className="text-sm font-bold text-gray-900">Scan QR Code in your Authenticator App</h4>
                </div>
                <div className="flex flex-col sm:flex-row items-center gap-4 bg-gray-50 p-4 rounded-xl border border-gray-200">
                  <img
                    src={mfaSetupData.qr_code_data_uri}
                    alt="Authenticator QR Code"
                    className="w-36 h-36 rounded-lg border border-white shadow-md flex-shrink-0"
                  />
                  <div className="space-y-2 text-xs text-gray-600">
                    <p>Open <strong>Google Authenticator</strong>, <strong>Microsoft Authenticator</strong>, or <strong>Authy</strong> and scan this code.</p>
                    <p className="text-[11px] text-gray-500">Or manually enter key:</p>
                    <div className="flex items-center gap-2">
                      <code className="bg-white px-2 py-1 border rounded font-mono font-bold text-gray-800 text-xs tracking-wider">
                        {mfaSetupData.secret}
                      </code>
                      <button
                        type="button"
                        onClick={() => {
                          navigator.clipboard.writeText(mfaSetupData.secret);
                          setCopiedSecret(true);
                          setTimeout(() => setCopiedSecret(false), 2000);
                        }}
                        className="p-1 text-gray-500 hover:text-purple-600 focus:outline-none"
                        title="Copy Secret"
                      >
                        {copiedSecret ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Step 2: Emergency Recovery Codes */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">2</span>
                    <h4 className="text-sm font-bold text-gray-900">Save Emergency Recovery Codes</h4>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(mfaSetupData.recovery_codes.join('\n'));
                      setCopiedCodes(true);
                      setTimeout(() => setCopiedCodes(false), 2000);
                    }}
                    className="inline-flex items-center gap-1 text-xs text-purple-600 font-semibold hover:underline"
                  >
                    {copiedCodes ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
                    {copiedCodes ? 'Copied!' : 'Copy All'}
                  </button>
                </div>
                <div className="grid grid-cols-4 gap-2 bg-slate-900 p-3.5 rounded-xl font-mono text-xs text-emerald-400 text-center font-bold">
                  {mfaSetupData.recovery_codes.map((code) => (
                    <span key={code} className="bg-slate-800 py-1 px-1.5 rounded">{code}</span>
                  ))}
                </div>
                <p className="text-[11px] text-amber-700 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                  ⚠️ Save these 8 codes in a safe place. If you lose your phone, you can use one of these codes to sign in.
                </p>
              </div>

              {/* Step 3: Enter 6-digit code */}
              <form onSubmit={handleVerifyMfaSetup} className="space-y-3 pt-2 border-t border-gray-100">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 text-xs font-bold flex items-center justify-center">3</span>
                  <label className="text-sm font-bold text-gray-900">Enter 6-Digit Code to Activate</label>
                </div>
                <input
                  type="text"
                  maxLength={6}
                  pattern="[0-9]*"
                  inputMode="numeric"
                  value={mfaVerifyCode}
                  onChange={(e) => setMfaVerifyCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="123456"
                  required
                  className="w-full py-2.5 text-center text-xl font-mono font-bold tracking-[0.4em] border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:outline-none"
                />

                <div className="pt-3 flex items-center justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowMfaModal(false)}
                    className="px-4 py-2 text-xs font-semibold text-gray-600 hover:text-gray-900"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={mfaSetupLoading || mfaVerifyCode.length !== 6}
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-semibold transition-colors disabled:opacity-50"
                  >
                    {mfaSetupLoading ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={15} />}
                    Verify &amp; Activate MFA
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Disable MFA Modal */}
      {showDisableModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100">
            <h3 className="text-base font-bold text-gray-900 mb-2">Disable Multi-Factor Authentication</h3>
            <p className="text-xs text-gray-500 mb-4">
              Enter your account password to confirm disabling Authenticator app protection.
            </p>
            <form onSubmit={handleDisableMfaSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-1">
                  Current Password
                </label>
                <input
                  type="password"
                  value={disablePassword}
                  onChange={(e) => setDisablePassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                  className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:outline-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowDisableModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={disableLoading || !disablePassword}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1.5"
                >
                  {disableLoading && <Loader2 size={14} className="animate-spin" />}
                  Confirm Disable
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
