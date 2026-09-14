import { statusColorClass } from '@/utils/formatters';

interface StatusBadgeProps {
  status: string;
  label?: string;
  size?: 'sm' | 'md';
}

const STATUS_LABELS: Record<string, string> = {
  PASS:      'Pass',
  FAIL:      'Fail',
  ABSENT:    'Absent',
  WITHHELD:  'Withheld',
  ACTIVE:    'Active',
  INACTIVE:  'Inactive',
  COMPLETED: 'Completed',
  PENDING:   'Pending',
  FAILED:    'Failed',
};

export function StatusBadge({ status, label, size = 'sm' }: StatusBadgeProps) {
  const displayLabel = label ?? STATUS_LABELS[status] ?? status;
  const colorClass   = statusColorClass(status);
  const sizeClass    = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center rounded-full border font-medium ${colorClass} ${sizeClass}`}
      aria-label={displayLabel}
    >
      {displayLabel}
    </span>
  );
}
