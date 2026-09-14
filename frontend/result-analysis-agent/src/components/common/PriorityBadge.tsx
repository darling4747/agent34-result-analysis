import type { PriorityLevel } from '@/types/analysis';
import { priorityColorClass, priorityDotClass, priorityLabel } from '@/utils/formatters';

interface PriorityBadgeProps {
  level: PriorityLevel;
  showDot?: boolean;
  size?: 'sm' | 'md';
}

export function PriorityBadge({ level, showDot = true, size = 'sm' }: PriorityBadgeProps) {
  const colorClass = priorityColorClass(level);
  const dotClass   = priorityDotClass(level);
  const sizeClass  = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-sm';

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${colorClass} ${sizeClass}`}
      aria-label={`Priority: ${priorityLabel(level)}`}
    >
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${dotClass}`} aria-hidden="true" />
      )}
      {priorityLabel(level)}
    </span>
  );
}
