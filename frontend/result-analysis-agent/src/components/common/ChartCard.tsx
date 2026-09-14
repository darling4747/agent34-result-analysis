import { EmptyState } from './EmptyState';
import React from 'react';

interface ChartCardProps {
  title: string;
  subtitle?: string;
  isEmpty?: boolean;
  emptyMessage?: string;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  minHeight?: number;
}

export function ChartCard({
  title,
  subtitle,
  isEmpty = false,
  emptyMessage = 'No data available for the selected filters.',
  actions,
  children,
  className = '',
  minHeight = 260,
}: ChartCardProps) {
  return (
    <section
      className={`bg-white rounded-lg border border-gray-200 p-4 shadow-sm ${className}`}
      aria-label={title}
    >
      <div className="flex items-start justify-between gap-2 mb-4">
        <div>
          <h2 className="text-sm font-semibold text-gray-800">{title}</h2>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        {actions && <div className="flex-shrink-0">{actions}</div>}
      </div>

      {isEmpty ? (
        <EmptyState
          title="No data"
          description={emptyMessage}
          className="py-10"
        />
      ) : (
        <div style={{ minHeight }}>{children}</div>
      )}
    </section>
  );
}
