import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { PageSkeleton } from '@/components/common/LoadingSkeleton';
import { canAccessPage } from '@/utils/rbac';
import Unauthorized from '@/pages/Unauthorized';

/**
 * Wraps protected routes.
 * - Unauthenticated  -> /login
 * - must_change_password -> /change-password
 * - Unauthorized role -> <Unauthorized /> 403 screen
 * - Authenticated + authorized -> render children
 */
export function ProtectedRoute() {
  const { user, isAuthenticated, mustChangePassword, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="w-full max-w-4xl px-6">
          <PageSkeleton />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (mustChangePassword) {
    return <Navigate to="/change-password" replace />;
  }

  if (!canAccessPage(user?.role, location.pathname)) {
    return <Unauthorized />;
  }

  return <Outlet />;
}
