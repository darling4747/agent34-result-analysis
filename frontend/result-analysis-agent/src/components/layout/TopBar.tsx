import { Bell, ChevronDown, Menu, LogOut } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { ACADEMIC_YEARS, CURRENT_ACADEMIC_YEAR, CURRENT_SEMESTER, DEPARTMENTS, NAV_ITEMS, SEMESTERS } from '@/utils/constants';

interface TopBarProps {
  onMenuClick: () => void;
}

function usePageMeta() {
  const location = useLocation();
  const match = NAV_ITEMS.find(
    (n) => n.path === location.pathname || (n.path !== '/dashboard' && location.pathname.startsWith(n.path))
  );
  return { title: match?.label ?? 'Result Analysis Agent', path: match?.path ?? '/dashboard' };
}

export function TopBar({ onMenuClick }: TopBarProps) {
  const { title } = usePageMeta();
  const { user, logout } = useAuth();
  const userInitials = user?.full_name
    ? user.full_name.split(' ').map((w) => w[0]).slice(0, 2).join('').toUpperCase()
    : 'PA';
  const userRole = typeof user?.role === 'string' ? user.role : ((user?.role as any)?.name ?? 'PLATFORM_ADMIN');

  const [year, setYear] = useState(CURRENT_ACADEMIC_YEAR);
  const [sem, setSem] = useState(CURRENT_SEMESTER);
  const [dept, setDept] = useState(DEPARTMENTS[0]);
  const [notifOpen, setNotifOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const notifRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') {
        setUserMenuOpen(false);
        setNotifOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4 gap-3 flex-shrink-0 z-20 relative">
      {/* Mobile menu toggle */}
      <button
        onClick={onMenuClick}
        className="lg:hidden text-gray-500 hover:text-gray-800 p-1.5 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
        aria-label="Open navigation"
      >
        <Menu size={20} aria-hidden="true" />
      </button>

      {/* Page title */}
      <div className="flex-1 min-w-0">
        <h1 className="text-sm font-semibold text-gray-900 truncate">{title}</h1>
      </div>

      {/* Context selectors */}
      <div className="hidden sm:flex items-center gap-2">
        <ContextSelect
          value={year}
          onChange={setYear}
          options={ACADEMIC_YEARS}
          label="Academic year"
          formatLabel={(v) => `AY ${v}`}
        />
        <ContextSelect
          value={String(sem)}
          onChange={(v) => setSem(Number(v))}
          options={SEMESTERS.map(String)}
          label="Semester"
          formatLabel={(v) => `Sem ${v}`}
        />
        <ContextSelect
          value={dept}
          onChange={setDept}
          options={DEPARTMENTS}
          label="Department"
          formatLabel={(v) => v.split(' ')[0]}
        />
      </div>

      {/* Notifications */}
      <div className="relative" ref={notifRef}>
        <button
          onClick={() => {
            setNotifOpen((o) => !o);
            setUserMenuOpen(false);
          }}
          className="relative text-gray-500 hover:text-gray-800 p-1.5 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
          aria-label="Notifications (2 unread)"
          aria-expanded={notifOpen}
        >
          <Bell size={18} aria-hidden="true" />
          <span
            className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"
            aria-hidden="true"
          />
        </button>

        {notifOpen && (
          <div
            className="absolute right-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
            role="dialog"
            aria-label="Notifications"
          >
            <div className="px-3 py-2 border-b border-gray-100">
              <h2 className="text-xs font-semibold text-gray-700 uppercase tracking-wide">Notifications</h2>
            </div>
            <ul className="divide-y divide-gray-100">
              {[
                { text: 'CS606 flagged as CRITICAL priority', time: '2 min ago', dot: 'bg-red-500' },
                { text: 'Result upload completed — 7 warnings', time: '18 min ago', dot: 'bg-yellow-500' },
              ].map((n, i) => (
                <li key={i} className="flex items-start gap-2.5 px-3 py-2.5 hover:bg-gray-50">
                  <span className={`mt-1.5 w-2 h-2 rounded-full flex-shrink-0 ${n.dot}`} aria-hidden="true" />
                  <div>
                    <p className="text-xs text-gray-800">{n.text}</p>
                    <p className="text-[11px] text-gray-400 mt-0.5">{n.time}</p>
                  </div>
                </li>
              ))}
            </ul>
            <div className="px-3 py-2 border-t border-gray-100">
              <button
                onClick={() => setNotifOpen(false)}
                className="text-xs text-blue-600 hover:text-blue-800 focus:outline-none cursor-pointer"
              >
                Dismiss all
              </button>
            </div>
          </div>
        )}
      </div>

      {/* User profile dropdown (PA Avatar) */}
      <div className="relative" ref={userMenuRef}>
        <button
          onClick={() => {
            setUserMenuOpen((o) => !o);
            setNotifOpen(false);
          }}
          className="flex items-center gap-1.5 text-gray-700 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-md px-1.5 py-1 cursor-pointer transition-colors"
          aria-label={`User menu for ${user?.full_name || 'Platform Administrator'}`}
          aria-haspopup="true"
          aria-expanded={userMenuOpen}
        >
          <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-[11px] font-semibold flex-shrink-0 shadow-xs">
            {userInitials}
          </div>
          <ChevronDown
            size={14}
            className={`transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`}
            aria-hidden="true"
          />
        </button>

        {userMenuOpen && (
          <div
            className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-xl py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-150"
            role="menu"
            aria-orientation="vertical"
            aria-label="User profile options"
          >
            <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50">
              <p className="font-semibold text-xs text-gray-900 truncate">{user?.full_name || 'Platform Administrator'}</p>
              <p className="text-[11px] text-gray-500 truncate mt-0.5">{user?.email || 'admin@university.edu'}</p>
              <span className="inline-block mt-1.5 px-2 py-0.5 bg-blue-100 text-blue-800 text-[10px] font-bold rounded uppercase tracking-wider">
                {userRole}
              </span>
            </div>

            <div className="py-1">
              <button
                onClick={() => {
                  setUserMenuOpen(false);
                  void logout();
                }}
                className="w-full text-left px-4 py-2 text-xs text-red-600 hover:bg-red-50 flex items-center gap-2 font-medium cursor-pointer transition-colors"
                role="menuitem"
              >
                <LogOut size={14} aria-hidden="true" />
                Sign Out
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

interface ContextSelectProps {
  value: string;
  onChange: (v: string) => void;
  options: string[];
  label: string;
  formatLabel?: (v: string) => string;
}

function ContextSelect({ value, onChange, options, label, formatLabel }: ContextSelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label={label}
      className="border border-gray-200 rounded-md px-2 py-1 text-xs text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer"
    >
      {options.map((o) => (
        <option key={o} value={o}>
          {formatLabel ? formatLabel(o) : o}
        </option>
      ))}
    </select>
  );
}
