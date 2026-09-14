import { AlertCircle, RefreshCw, WifiOff } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  isNetworkError?: boolean;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title,
  message,
  isNetworkError = false,
  onRetry,
  className = '',
}: ErrorStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center py-12 px-6 text-center ${className}`}
      role="alert"
      aria-live="assertive"
    >
      <div className="mb-3 text-red-400" aria-hidden="true">
        {isNetworkError
          ? <WifiOff size={40} strokeWidth={1.5} />
          : <AlertCircle size={40} strokeWidth={1.5} />
        }
      </div>
      <h3 className="text-sm font-semibold text-gray-800 mb-1">
        {title ?? (isNetworkError ? 'Backend unavailable' : 'Unable to load data')}
      </h3>
      <p className="text-sm text-gray-500 max-w-sm mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-blue-600 border border-blue-200 rounded-md hover:bg-blue-50 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
          aria-label="Retry"
        >
          <RefreshCw size={14} aria-hidden="true" />
          Try again
        </button>
      )}
    </div>
  );
}
