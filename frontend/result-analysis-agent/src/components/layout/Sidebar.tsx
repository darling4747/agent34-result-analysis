import {
  AlertTriangle, BookOpen, FileText, History, LayoutDashboard,
  Layers, LineChart, LogOut, Shield, Sparkles, TrendingUp, Trophy,
  Upload, Users, UserCheck, X, Activity, Settings,
} from 'lucide-react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { getVisibleNavigationSections } from '@/utils/rbac';

const ICON_MAP: Record<string, React.ReactNode> = {
  LayoutDashboard: <LayoutDashboard size={16} aria-hidden="true" />,
  Upload:          <Upload size={16} aria-hidden="true" />,
  BookOpen:        <BookOpen size={16} aria-hidden="true" />,
  Layers:          <Layers size={16} aria-hidden="true" />,
  Users:           <Users size={16} aria-hidden="true" />,
  Trophy:          <Trophy size={16} aria-hidden="true" />,
  TrendingUp:      <TrendingUp size={16} aria-hidden="true" />,
  LineChart:       <LineChart size={16} aria-hidden="true" />,
  AlertTriangle:   <AlertTriangle size={16} aria-hidden="true" />,
  FileText:        <FileText size={16} aria-hidden="true" />,
  History:         <History size={16} aria-hidden="true" />,
  Sparkles:        <Sparkles size={16} aria-hidden="true" />,
  UserCheck:       <UserCheck size={16} aria-hidden="true" />,
  Settings:        <Settings size={16} aria-hidden="true" />,
  Shield:          <Shield size={16} aria-hidden="true" />,
};

const ROLE_LABELS: Record<string, string> = {
  PLATFORM_ADMIN: 'Platform Admin',
  DEAN:           'Dean',
  HOD:            'Head of Department',
  FACULTY:        'Faculty',
  IQAC:           'IQAC',
  MANAGEMENT:     'Management',
  AUDITOR:        'Auditor',
};

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export function Sidebar({ open, onClose }: SidebarProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const sections = getVisibleNavigationSections(user?.role);

  const initials = user?.full_name
    ? user.full_name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
    : 'U';

  async function handleLogout() {
    await logout();
    navigate('/login', { replace: true });
  }

  return (
    <>
      {open && (
        <div className="fixed inset-0 z-20 bg-black/40 lg:hidden" onClick={onClose} aria-hidden="true" />
      )}
      <aside
        className={`
          fixed top-0 left-0 z-30 h-full w-60 bg-gray-900 flex flex-col
          transition-transform duration-200
          ${open ? 'translate-x-0' : '-translate-x-full'}
          lg:relative lg:translate-x-0 lg:z-auto lg:flex-shrink-0
        `}
        aria-label="Main navigation"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center flex-shrink-0">
              <Activity size={15} className="text-white" aria-hidden="true" />
            </div>
            <div>
              <div className="text-sm font-semibold text-white leading-tight">Agent 34</div>
              <div className="text-[10px] text-gray-400 leading-tight">Result Analysis</div>
            </div>
          </div>
          <button onClick={onClose} className="lg:hidden text-gray-400 hover:text-white p-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" aria-label="Close navigation">
            <X size={16} aria-hidden="true" />
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-3 scrollbar-thin space-y-4" aria-label="Sections">
          {sections.map((section) => (
            <div key={section.title} className="px-2">
              {section.title !== 'OVERVIEW' && (
                <div className="px-3 pb-1 text-[10px] font-semibold text-gray-500 tracking-wider uppercase">
                  {section.title}
                </div>
              )}
              <ul role="list" className="flex flex-col gap-0.5">
                {section.items.map((item) => {
                  const isActive = location.pathname === item.path ||
                    (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
                  return (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        onClick={() => { if (window.innerWidth < 1024) onClose(); }}
                        className={`
                          flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors
                          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset
                          ${isActive ? 'bg-blue-700 text-white font-medium' : 'text-gray-400 hover:text-white hover:bg-gray-800'}
                        `}
                        aria-current={isActive ? 'page' : undefined}
                      >
                        <span className="flex-shrink-0">{ICON_MAP[item.icon]}</span>
                        <span>{item.label}</span>
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-gray-800 px-3 py-3 flex flex-col gap-2">
          <div className="flex items-center gap-2 px-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 flex-shrink-0" aria-hidden="true" />
            <span className="text-xs text-gray-400">System operational</span>
          </div>
          {user?.department && (
            <div className="text-[11px] text-gray-500 px-2 leading-tight">
              Dept: {user.department}
            </div>
          )}
          <div className="flex items-center justify-between mt-1 px-2">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center text-white text-[10px] font-semibold flex-shrink-0">
                {initials}
              </div>
              <div className="min-w-0">
                <div className="text-xs text-white font-medium leading-tight truncate max-w-[120px]">
                  {user?.full_name ?? 'User'}
                </div>
                <div className="text-[10px] text-gray-500 leading-tight">
                  {user?.role ? ROLE_LABELS[user.role] ?? user.role : ''}
                </div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="text-gray-500 hover:text-red-400 transition-colors p-1 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 flex-shrink-0"
              aria-label="Sign out"
              title="Sign out"
            >
              <LogOut size={14} aria-hidden="true" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}