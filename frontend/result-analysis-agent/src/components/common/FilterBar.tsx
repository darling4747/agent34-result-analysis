import { ACADEMIC_YEARS, DEPARTMENTS, PROGRAMMES, SEMESTERS } from '@/utils/constants';
import type { ResultFilters } from '@/types/result';

interface FilterBarProps {
  filters: ResultFilters;
  onChange: (updated: Partial<ResultFilters>) => void;
  show?: {
    academicYear?: boolean;
    semester?: boolean;
    department?: boolean;
    programme?: boolean;
    batch?: boolean;
    section?: boolean;
    course?: boolean;
  };
  courseOptions?: { code: string; name: string }[];
  sectionOptions?: string[];
  batchOptions?: string[];
  className?: string;
}

interface SelectProps {
  label: string;
  value: string | number | undefined;
  onChange: (val: string) => void;
  options: { value: string | number; label: string }[];
  placeholder?: string;
}

function FilterSelect({ label, value, onChange, options, placeholder = 'All' }: SelectProps) {
  return (
    <div className="flex flex-col gap-1 min-w-[140px]">
      <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</label>
      <select
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        className="border border-gray-200 rounded-md px-2.5 py-1.5 text-sm bg-white text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        aria-label={label}
      >
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

export function FilterBar({
  filters,
  onChange,
  show = { academicYear: true, semester: true, department: true },
  courseOptions = [],
  sectionOptions = [],
  batchOptions = ['2024', '2023', '2022', '2021', '2020'],
  className = '',
}: FilterBarProps) {
  return (
    <div
      className={`flex flex-wrap items-end gap-3 p-3 bg-gray-50 border border-gray-200 rounded-lg ${className}`}
      role="search"
      aria-label="Result filters"
    >
      {show.academicYear && (
        <FilterSelect
          label="Academic Year"
          value={filters.academicYear}
          onChange={(v) => onChange({ academicYear: v || undefined })}
          options={ACADEMIC_YEARS.map((y) => ({ value: y, label: y }))}
        />
      )}
      {show.semester && (
        <FilterSelect
          label="Semester"
          value={filters.semester}
          onChange={(v) => onChange({ semester: v ? Number(v) : undefined })}
          options={SEMESTERS.map((s) => ({ value: s, label: `Semester ${s}` }))}
        />
      )}
      {show.department && (
        <FilterSelect
          label="Department"
          value={filters.department}
          onChange={(v) => onChange({ department: v || undefined })}
          options={DEPARTMENTS.map((d) => ({ value: d, label: d.replace('Engineering', 'Engg.') }))}
        />
      )}
      {show.programme && (
        <FilterSelect
          label="Programme"
          value={filters.programme}
          onChange={(v) => onChange({ programme: v || undefined })}
          options={PROGRAMMES.map((p) => ({ value: p, label: p }))}
        />
      )}
      {show.batch && (
        <FilterSelect
          label="Batch"
          value={filters.batch}
          onChange={(v) => onChange({ batch: v || undefined })}
          options={batchOptions.map((b) => ({ value: b, label: `Batch ${b}` }))}
        />
      )}
      {show.section && sectionOptions.length > 0 && (
        <FilterSelect
          label="Section"
          value={filters.section}
          onChange={(v) => onChange({ section: v || undefined })}
          options={sectionOptions.map((s) => ({ value: s, label: `Section ${s}` }))}
        />
      )}
      {show.course && courseOptions.length > 0 && (
        <FilterSelect
          label="Course"
          value={filters.courseCode}
          onChange={(v) => onChange({ courseCode: v || undefined })}
          options={courseOptions.map((c) => ({ value: c.code, label: `${c.code} — ${c.name}` }))}
        />
      )}
    </div>
  );
}
