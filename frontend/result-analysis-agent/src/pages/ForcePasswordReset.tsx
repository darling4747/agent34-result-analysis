import { AlertCircle, CheckCircle2, Eye, EyeOff, KeyRound, Loader2, Lock } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { changeInitialPassword } from '@/api/authApi';
import { useAuth } from '@/contexts/AuthContext';
import { ApiError } from '@/api/client';

const PASSWORD_RULES = [
  { id: 'len',     label: 'At least 12 characters',         test: (p: string) => p.length >= 12 },
  { id: 'upper',   label: 'At least one uppercase letter',  test: (p: string) => /[A-Z]/.test(p) },
  { id: 'lower',   label: 'At least one lowercase letter',  test: (p: string) => /[a-z]/.test(p) },
  { id: 'digit',   label: 'At least one digit',             test: (p: string) => /\d/.test(p) },
  { id: 'special', label: 'At least one special character', test: (p: string) => /[!@#$%^&*()\-_=+]/.test(p) },
];

export default function ForcePasswordReset() {
  const { clearAuth } = useAuth();
  const navigate = useNavigate();
  const [currentPw, setCurrentPw]     = useState('');
  const [newPw, setNewPw]             = useState('');
  const [confirmPw, setConfirmPw]     = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew]         = useState(false);
  const [error, setError]             = useState<string | null>(null);
  const [loading, setLoading]         = useState(false);
  const rules = PASSWORD_RULES.map((r) => ({ ...r, passed: r.test(newPw) }));
  const passwordsMatch = newPw.length > 0 && newPw === confirmPw;
  const allPassed = rules.every((r) => r.passed) && passwordsMatch;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!allPassed || !currentPw) return;
    setError(null); setLoading(true);
    try {
      const result = await changeInitialPassword({ current_password: currentPw, new_password: newPw, confirm_password: confirmPw });
      localStorage.setItem('agent34_token', result.data.access_token);
      navigate('/dashboard', { replace: true });
      window.location.reload();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Password change failed.');
    } finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen tech-bg flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-amber-500 mb-4">
            <KeyRound size={28} className="text-white" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Password Reset Required</h1>
          <p className="text-sm text-gray-500 mt-1">Your account uses a temporary password. Set a permanent one before continuing.</p>
        </div>
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
          {error && (
            <div className="flex items-start gap-2 p-3 mb-4 bg-red-50 border border-red-200 rounded-md" role="alert">
              <AlertCircle size={14} className="text-red-500 mt-0.5" />
              <span className="text-sm text-red-700">{error}</span>
            </div>
          )}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
            <div className="flex flex-col gap-1">
              <label htmlFor="current-pw" className="text-xs font-medium text-gray-600 uppercase tracking-wide">Temporary Password</label>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input id="current-pw" type={showCurrent ? "text" : "password"} value={currentPw} onChange={(e) => setCurrentPw(e.target.value)}
                  placeholder="Enter temporary password" required disabled={loading}
                  className="w-full pl-9 pr-10 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50" />
                <button type="button" onClick={() => setShowCurrent((v) => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showCurrent ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="new-pw" className="text-xs font-medium text-gray-600 uppercase tracking-wide">New Password</label>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input id="new-pw" type={showNew ? "text" : "password"} value={newPw} onChange={(e) => setNewPw(e.target.value)}
                  placeholder="Enter new password" required disabled={loading}
                  className="w-full pl-9 pr-10 py-2.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50" />
                <button type="button" onClick={() => setShowNew((v) => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                  {showNew ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {newPw.length > 0 && (
                <ul className="mt-2 flex flex-col gap-1">
                  {rules.map((r) => (
                    <li key={r.id} className={`flex items-center gap-1.5 text-xs ${r.passed ? 'text-emerald-600' : 'text-gray-500'}`}>
                      <CheckCircle2 size={11} className={r.passed ? "text-emerald-500" : "text-gray-300"} aria-hidden="true" />
                      {r.label}
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="confirm-pw" className="text-xs font-medium text-gray-600 uppercase tracking-wide">Confirm New Password</label>
              <input
                id="confirm-pw"
                type="password"
                value={confirmPw}
                onChange={(e) => setConfirmPw(e.target.value)}
                placeholder="Repeat new password"
                required
                disabled={loading}
                className={`w-full px-3 py-2.5 text-sm border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 ${confirmPw.length > 0 ? (passwordsMatch ? 'border-emerald-400' : 'border-red-300') : 'border-gray-200'}`}
              />
              {confirmPw.length > 0 && !passwordsMatch && (
                <p className="text-xs text-red-600 mt-0.5">Passwords do not match.</p>
              )}
            </div>
            <button type="submit" disabled={loading || !allPassed || !currentPw}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed mt-2">
              {loading && <Loader2 size={14} className="animate-spin" />}
              {loading ? 'Updating…' : 'Set Permanent Password'}
            </button>
          </form>
          <div className="mt-5 pt-4 border-t border-gray-100">
            <button onClick={() => { clearAuth(); window.location.href = '/login'; }}
              className="w-full text-xs text-gray-400 hover:text-gray-600">
              Sign out and log in with a different account
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
