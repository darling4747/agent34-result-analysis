import { TrendingDown, TrendingUp } from 'lucide-react';
import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: number;          // positive = improvement, negative = decline
  changeLabel?: string;
  icon?: React.ReactNode;
  accent?: 'blue' | 'green' | 'red' | 'orange' | 'purple' | 'gray';
  tooltip?: string;
  className?: string;
}

const accentBorder: Record<string, string> = {
  blue:   'border-l-blue-500',
  green:  'border-l-emerald-500',
  red:    'border-l-red-500',
  orange: 'border-l-orange-500',
  purple: 'border-l-purple-500',
  gray:   'border-l-gray-400',
};

const accentIcon: Record<string, string> = {
  blue:   'bg-blue-50 text-blue-600',
  green:  'bg-emerald-50 text-emerald-600',
  red:    'bg-red-50 text-red-600',
  orange: 'bg-orange-50 text-orange-600',
  purple: 'bg-purple-50 text-purple-600',
  gray:   'bg-gray-100 text-gray-500',
};

export const StatCard = React.memo(function StatCard({
  title,
  value,
  subtitle,
  change,
  changeLabel,
  icon,
  accent = 'blue',
  tooltip,
  className = '',
}: StatCardProps) {
  const hasChange = change != null;
  const isPositive = (change ?? 0) >= 0;

  return (
    <div
      className={`bg-white rounded-lg border border-gray-200 border-l-4 ${accentBorder[accent]} p-4 flex flex-col gap-2 shadow-sm ${className}`}
      title={tooltip}
      role="figure"
      aria-label={`${title}: ${value}`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wide leading-tight">
          {title}
        </span>
        {icon && (
          <span className={`flex-shrink-0 p-1.5 rounded-md ${accentIcon[accent]}`} aria-hidden="true">
            {icon}
          </span>
        )}
      </div>

      <div className="text-2xl font-semibold text-gray-900 leading-none">
        {value}
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {subtitle && (
          <span className="text-xs text-gray-500">{subtitle}</span>
        )}
        {hasChange && (
          <span
            className={`inline-flex items-center gap-0.5 text-xs font-medium ${
              isPositive ? 'text-emerald-600' : 'text-red-600'
            }`}
            aria-label={`${isPositive ? 'Increase' : 'Decrease'} of ${Math.abs(change!).toFixed(1)}%`}
          >
            {isPositive
              ? <TrendingUp size={12} aria-hidden="true" />
              : <TrendingDown size={12} aria-hidden="true" />}
            {isPositive ? '+' : ''}{change!.toFixed(1)}%
            {changeLabel && <span className="text-gray-400 font-normal">{changeLabel}</span>}
          </span>
        )}
      </div>
    </div>
  );
});
