import { Activity, AlertCircle, Eye, EyeOff, Loader2, Lock, Mail, ShieldCheck, KeyRound, ArrowLeft } from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { verifyMfaLogin } from '@/api/authApi';
import { ApiError } from '@/api/client';

export default function Login() {
  const { login, completeMfaLogin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname ?? '/dashboard';

  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw]     = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [loading, setLoading]   = useState(false);

  // MFA Challenge state
  const [mfaChallenge, setMfaChallenge] = useState<{ mfa_token: string; email: string } | null>(null);
  const [totpCode, setTotpCode]         = useState('');
  const [recoveryCode, setRecoveryCode] = useState('');
  const [useRecovery, setUseRecovery]   = useState(false);
  const [mfaLoading, setMfaLoading]     = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password) return;
    setError(null);
    setLoading(true);
    try {
      const result = await login(email.trim(), password);
      if (result.mfa_required && result.mfa_token) {
        setMfaChallenge({ mfa_token: result.mfa_token, email: email.trim() });
      } else if (result.must_change_password) {
        navigate('/change-password', { replace: true });
      } else {
        navigate(from, { replace: true });
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Unable to connect to the server.');
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleMfaVerify(e: React.FormEvent) {
    e.preventDefault();
    if (!mfaChallenge) return;
    setError(null);
    setMfaLoading(true);
    try {
      const resp = await verifyMfaLogin(
        mfaChallenge.mfa_token,
        useRecovery ? undefined : totpCode.trim(),
        useRecovery ? recoveryCode.trim() : undefined,
      );
      if (resp.data.access_token) {
        completeMfaLogin(resp.data);
        if (resp.data.must_change_password) {
          navigate('/change-password', { replace: true });
        } else {
          navigate(from, { replace: true });
        }
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Verification failed. Invalid authenticator or recovery code.');
      }
    } finally {
      setMfaLoading(false);
    }
  }

  return (
    <div className="min-h-screen tech-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-blue-600 mb-4">
            <Activity size={28} className="text-white" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Agent 34</h1>
          <p className="text-sm text-gray-500 mt-1">Result Analysis Agent</p>
          <p className="text-xs text-gray-400 mt-0.5">Agentic AI Platform for Academic Institutions</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
          {mfaChallenge ? (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <button
                  type="button"
                  onClick={() => { setMfaChallenge(null); setError(null); }}
                  className="text-gray-400 hover:text-gray-600 focus:outline-none p-1 rounded"
                  title="Back to login"
                >
                  <ArrowLeft size={16} />
                </button>
                <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center font-bold">
                  <ShieldCheck size={18} />
                </div>
                <div>
                  <h2 className="text-base font-bold text-gray-900">Two-Factor Authentication</h2>
                  <p className="text-xs text-gray-500">Security verification required for your account</p>
                </div>
              </div>

              {error && (
                <div className="flex items-start gap-2.5 p-3 my-4 bg-red-50 border border-red-200 rounded-md">
                  <AlertCircle size={15} className="text-red-500 flex-shrink-0 mt-0.5" />
                  <span className="text-xs text-red-700">{error}</span>
                </div>
              )}

              <form onSubmit={handleMfaVerify} className="mt-5 space-y-4">
                {!useRecovery ? (
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                      6-Digit Authenticator Code
                    </label>
                    <div className="relative">
                      <KeyRound size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        maxLength={6}
                        pattern="[0-9]*"
                        inputMode="numeric"
                        autoFocus
                        value={totpCode}
                        onChange={(e) => setTotpCode(e.target.value.replace(/\D/g, ''))}
                        placeholder="123456"
                        required
                        className="w-full pl-9 pr-3 py-2.5 text-center text-lg tracking-[0.4em] font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:outline-none font-bold text-gray-900"
                      />
                    </div>
                    <p className="text-[11px] text-gray-400 mt-1.5 text-center">
                      Enter code from Google Authenticator, Authy, or Microsoft Authenticator
                    </p>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 uppercase tracking-wider mb-2">
                      Emergency Recovery Code
                    </label>
                    <input
                      type="text"
                      autoFocus
                      value={recoveryCode}
                      onChange={(e) => setRecoveryCode(e.target.value)}
                      placeholder="XXXX-XXXX"
                      required
                      className="w-full px-3 py-2.5 text-center text-base font-mono border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:outline-none uppercase font-bold text-gray-900"
                    />
                    <p className="text-[11px] text-gray-400 mt-1.5 text-center">
                      Enter one of your 8-character single-use recovery codes
                    </p>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={mfaLoading || (!useRecovery && totpCode.length !== 6) || (useRecovery && !recoveryCode.trim())}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                >
                  {mfaLoading ? <Loader2 size={16} className="animate-spin" /> : <ShieldCheck size={16} />}
                  Verify &amp; Continue
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => { setUseRecovery(!useRecovery); setError(null); }}
                    className="text-xs text-purple-600 hover:text-purple-800 font-semibold underline"
                  >
                    {useRecovery ? 'Use authenticator app code instead' : 'Use emergency recovery code'}
                  </button>
                </div>
              </form>
            </div>
          ) : (
            <div>
              <h2 className="text-base font-semibold text-gray-800 mb-6">Sign in to your account</h2>

              {error && (
                <div
                  className="flex items-start gap-2.5 p-3 mb-5 bg-red-50 border border-red-200 rounded-md"
                  role="alert"
                  aria-live="assertive"
                >
                  <AlertCircle size={15} className="text-red-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <span className="text-sm text-red-700">{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
                {/* Email */}
                <div className="flex flex-col gap-1">
                  <label htmlFor="email" className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                    Email address
                  </label>
                  <div className="relative">
                    <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
                    <input
                      id="email"
                      type="email"
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="hod.cse@university.edu"
                      required
                      disabled={loading}
                      className="w-full pl-9 pr-3 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
                    />
                  </div>
                </div>

                {/* Password */}
                <div className="flex flex-col gap-1">
                  <label htmlFor="password" className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                    Password
                  </label>
                  <div className="relative">
                    <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" aria-hidden="true" />
                    <input
                      id="password"
                      type={showPw ? 'text' : 'password'}
                      autoComplete="current-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter password"
                      required
                      disabled={loading}
                      className="w-full pl-9 pr-10 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-50 disabled:text-gray-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPw((v) => !v)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
                      aria-label={showPw ? 'Hide password' : 'Show password'}
                    >
                      {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading || !email.trim() || !password}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
                >
                  {loading && <Loader2 size={15} className="animate-spin" aria-hidden="true" />}
                  {loading ? 'Signing in…' : 'Sign in'}
                </button>
              </form>
            </div>
          )}

          <div className="mt-6 pt-5 border-t border-gray-100">
            <p className="text-xs text-gray-400 text-center">
              Account access is managed by your Platform Administrator.
              <br />Contact them if you need account assistance.
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Agent 34 · Result Analysis · Vignan University Platform
        </p>
      </div>
    </div>
  );
}
