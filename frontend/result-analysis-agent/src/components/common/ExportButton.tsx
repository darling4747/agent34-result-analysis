import { Download, Loader2 } from 'lucide-react';
import { useState } from 'react';

interface ExportButtonProps {
  label?: string;
  onExport: () => Promise<void>;
  disabled?: boolean;
  variant?: 'primary' | 'outline';
}

export function ExportButton({ label = 'Export', onExport, disabled = false, variant = 'outline' }: ExportButtonProps) {
  const [loading, setLoading] = useState(false);
  const [done, setDone]       = useState(false);

  async function handleClick() {
    if (loading || disabled) return;
    setLoading(true);
    setDone(false);
    try {
      await onExport();
      setDone(true);
      setTimeout(() => setDone(false), 3000);
    } finally {
      setLoading(false);
    }
  }

  const base = 'inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed';
  const cls = variant === 'primary'
    ? `${base} bg-blue-600 text-white hover:bg-blue-700`
    : `${base} border border-gray-200 text-gray-700 bg-white hover:bg-gray-50`;

  return (
    <button
      onClick={handleClick}
      disabled={loading || disabled}
      className={cls}
      aria-label={loading ? 'Exporting…' : done ? 'Export complete' : label}
    >
      {loading
        ? <Loader2 size={14} className="animate-spin" aria-hidden="true" />
        : <Download size={14} aria-hidden="true" />
      }
      {loading ? 'Exporting…' : done ? 'Done' : label}
    </button>
  );
}
