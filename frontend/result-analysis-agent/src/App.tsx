import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { DatasetProvider } from '@/contexts/DatasetContext';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AppLayout } from '@/components/layout/AppLayout';
import { PageSkeleton } from '@/components/common/LoadingSkeleton';

// Auth pages (not lazy — load immediately)
import Login from '@/pages/Login';
import ForcePasswordReset from '@/pages/ForcePasswordReset';

// Analytics pages (lazy-loaded for code-splitting)
const Dashboard           = lazy(() => import('@/pages/Dashboard'));
const UploadResults       = lazy(() => import('@/pages/UploadResults'));
const CourseAnalysis      = lazy(() => import('@/pages/CourseAnalysis'));
const SectionAnalysis     = lazy(() => import('@/pages/SectionAnalysis'));
const FacultyAnalysis     = lazy(() => import('@/pages/FacultyAnalysis'));
const MeritList           = lazy(() => import('@/pages/MeritList'));
const CorrelationAnalysis = lazy(() => import('@/pages/CorrelationAnalysis'));
const HistoricalTrends    = lazy(() => import('@/pages/HistoricalTrends'));
const Interventions       = lazy(() => import('@/pages/Interventions'));
const Reports             = lazy(() => import('@/pages/Reports'));
const NotFound            = lazy(() => import('@/pages/NotFound'));
const AIInsights          = lazy(() => import('@/pages/AIInsights'));
const ImportHistory       = lazy(() => import('@/pages/ImportHistory'));
const UserManagement      = lazy(() => import('@/pages/UserManagement'));
const Settings            = lazy(() => import('@/pages/Settings'));
const AuditLogs           = lazy(() => import('@/pages/AuditLogs'));

function PageFallback() {
  return (
    <div className="px-4 sm:px-6 py-6 max-w-screen-2xl mx-auto">
      <PageSkeleton />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <DatasetProvider>
      <BrowserRouter>
        <Suspense fallback={<PageFallback />}>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/change-password" element={<ForcePasswordReset />} />

            {/* Root redirect */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* Protected analytics routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/dashboard"     element={<Dashboard />} />
                <Route path="/upload"        element={<UploadResults />} />
                <Route path="/courses"       element={<CourseAnalysis />} />
                <Route path="/sections"      element={<SectionAnalysis />} />
                <Route path="/faculty"       element={<FacultyAnalysis />} />
                <Route path="/merit-list"    element={<MeritList />} />
                <Route path="/correlation"   element={<CorrelationAnalysis />} />
                <Route path="/historical"    element={<HistoricalTrends />} />
                <Route path="/interventions" element={<Interventions />} />
                <Route path="/reports"          element={<Reports />} />
                <Route path="/ai-insights"      element={<AIInsights />} />
                <Route path="/import-history"   element={<ImportHistory />} />
                <Route path="/users"            element={<UserManagement />} />
                <Route path="/settings"         element={<Settings />} />
                <Route path="/audit-logs"       element={<AuditLogs />} />
              </Route>
            </Route>

            {/* 404 */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="*" element={<NotFound />} />
              </Route>
            </Route>
          </Routes>
        </Suspense>
      </BrowserRouter>
      </DatasetProvider>
    </AuthProvider>
  );
}
