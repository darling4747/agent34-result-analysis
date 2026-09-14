import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Unauthorized() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[70vh] flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center bg-gray-900 border border-gray-800 rounded-xl p-8 shadow-2xl">
        <div className="w-16 h-16 bg-red-900/30 text-red-400 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-800/50">
          <ShieldAlert size={32} />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">403 — Access Denied</h1>
        <p className="text-gray-400 text-sm mb-6 leading-relaxed">
          You do not have permission to access this module. Your current role does not grant access to this page.
        </p>
        <button
          onClick={() => navigate('/dashboard', { replace: true })}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm rounded-lg transition-colors shadow-lg shadow-blue-600/20"
        >
          <ArrowLeft size={16} />
          Return to Dashboard
        </button>
      </div>
    </div>
  );
}

export default Unauthorized;
