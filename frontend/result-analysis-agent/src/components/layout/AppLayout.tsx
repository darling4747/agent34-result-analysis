import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { DatasetStatusBar } from '@/components/common/DatasetStatusBar';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden tech-bg">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar onMenuClick={() => setSidebarOpen(true)} />
        <DatasetStatusBar />

        <main
          id="main-content"
          className="flex-1 overflow-y-auto scrollbar-thin"
          tabIndex={-1}
          aria-label="Main content"
        >
          <div className="max-w-screen-2xl mx-auto px-4 sm:px-6 py-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
