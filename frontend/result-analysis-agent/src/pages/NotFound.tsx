import { ArrowLeft, FileQuestion } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
      <div className="text-gray-300 mb-4" aria-hidden="true">
        <FileQuestion size={64} strokeWidth={1.25} />
      </div>
      <h1 className="text-4xl font-bold text-gray-900 mb-2">404</h1>
      <h2 className="text-lg font-medium text-gray-700 mb-2">Page not found</h2>
      <p className="text-sm text-gray-500 max-w-sm mb-6">
        The page you are looking for does not exist or has been moved. Use the navigation to return to a known location.
      </p>
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
      >
        <ArrowLeft size={15} aria-hidden="true" />
        Return to Overview
      </Link>
    </div>
  );
}
