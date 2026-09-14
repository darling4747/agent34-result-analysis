import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, ChevronsUpDown, Search } from 'lucide-react';
import React, { useCallback, useMemo, useState } from 'react';
import { DEFAULT_PAGE_SIZE, PAGE_SIZE_OPTIONS } from '@/utils/constants';
import { EmptyState } from './EmptyState';

export interface Column<T> {
  key: string;
  header: string;
  accessor: (row: T) => React.ReactNode;
  sortValue?: (row: T) => string | number | null;
  className?: string;
  headerClassName?: string;
  width?: string;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  rowKey: (row: T) => string;
  searchable?: boolean;
  searchPlaceholder?: string;
  searchFilter?: (row: T, query: string) => boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  paginate?: boolean;
  defaultPageSize?: number;
  stickyHeader?: boolean;
  className?: string;
  caption?: string;
}

type SortDir = 'asc' | 'desc' | null;

export function DataTable<T>({
  columns,
  data,
  rowKey,
  searchable = false,
  searchPlaceholder = 'Search…',
  searchFilter,
  emptyTitle = 'No records found',
  emptyDescription,
  paginate = true,
  defaultPageSize = DEFAULT_PAGE_SIZE,
  stickyHeader = false,
  className = '',
  caption,
}: DataTableProps<T>) {
  const [query, setQuery]         = useState('');
  const [sortKey, setSortKey]     = useState<string | null>(null);
  const [sortDir, setSortDir]     = useState<SortDir>(null);
  const [page, setPage]           = useState(1);
  const [pageSize, setPageSize]   = useState(defaultPageSize);

  const filtered = useMemo(() => {
    if (!query.trim() || !searchFilter) return data;
    return data.filter((row) => searchFilter(row, query.toLowerCase()));
  }, [data, query, searchFilter]);

  const sorted = useMemo(() => {
    if (!sortKey || !sortDir) return filtered;
    const col = columns.find((c) => c.key === sortKey);
    if (!col?.sortValue) return filtered;
    return [...filtered].sort((a, b) => {
      const av = col.sortValue!(a) ?? '';
      const bv = col.sortValue!(b) ?? '';
      if (av < bv) return sortDir === 'asc' ? -1 : 1;
      if (av > bv) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filtered, sortKey, sortDir, columns]);

  const totalPages = paginate ? Math.max(1, Math.ceil(sorted.length / pageSize)) : 1;
  const safePage   = Math.min(page, totalPages);

  const paginated = useMemo(() => {
    if (!paginate) return sorted;
    const start = (safePage - 1) * pageSize;
    return sorted.slice(start, start + pageSize);
  }, [sorted, paginate, safePage, pageSize]);

  const handleSort = useCallback((key: string) => {
    setSortKey((prev) => {
      if (prev !== key) { setSortDir('asc'); return key; }
      setSortDir((d) => d === 'asc' ? 'desc' : d === 'desc' ? null : 'asc');
      return key;
    });
    setPage(1);
  }, []);

  const handleSearch = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setPage(1);
  }, []);

  function SortIcon({ colKey }: { colKey: string }) {
    if (!columns.find((c) => c.key === colKey)?.sortValue) return null;
    if (sortKey !== colKey || sortDir === null)
      return <ChevronsUpDown size={12} className="text-gray-400 flex-shrink-0" aria-hidden="true" />;
    if (sortDir === 'asc')
      return <ChevronUp size={12} className="text-blue-600 flex-shrink-0" aria-hidden="true" />;
    return <ChevronDown size={12} className="text-blue-600 flex-shrink-0" aria-hidden="true" />;
  }

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {searchable && (
        <div className="relative max-w-sm">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
            aria-hidden="true"
          />
          <input
            type="search"
            value={query}
            onChange={handleSearch}
            placeholder={searchPlaceholder}
            aria-label={searchPlaceholder}
            className="w-full pl-9 pr-3 py-1.5 text-sm border border-gray-200 rounded-md bg-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      )}

      <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full text-sm border-collapse" aria-label={caption}>
            {caption && <caption className="sr-only">{caption}</caption>}
            <thead className={`bg-gray-50 border-b border-gray-200 ${stickyHeader ? 'sticky top-0 z-10' : ''}`}>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    scope="col"
                    className={`px-4 py-2.5 text-left text-xs font-semibold text-gray-600 uppercase tracking-wide whitespace-nowrap ${col.sortValue ? 'cursor-pointer select-none hover:text-gray-900' : ''} ${col.headerClassName ?? ''}`}
                    style={col.width ? { width: col.width } : undefined}
                    onClick={col.sortValue ? () => handleSort(col.key) : undefined}
                    aria-sort={
                      sortKey === col.key
                        ? sortDir === 'asc' ? 'ascending' : sortDir === 'desc' ? 'descending' : 'none'
                        : undefined
                    }
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.header}
                      <SortIcon colKey={col.key} />
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paginated.length === 0 ? (
                <tr>
                  <td colSpan={columns.length}>
                    <EmptyState
                      title={emptyTitle}
                      description={emptyDescription}
                      className="py-12"
                    />
                  </td>
                </tr>
              ) : (
                paginated.map((row) => (
                  <tr
                    key={rowKey(row)}
                    className="border-b border-gray-100 hover:bg-gray-50 transition-colors last:border-0"
                  >
                    {columns.map((col) => (
                      <td
                        key={col.key}
                        className={`px-4 py-2.5 text-gray-700 ${col.className ?? ''}`}
                      >
                        {col.accessor(row)}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {paginate && sorted.length > 0 && (
        <div className="flex items-center justify-between gap-4 flex-wrap text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <span>Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              className="border border-gray-200 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Rows per page"
            >
              {PAGE_SIZE_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <span className="text-gray-500">
              {((safePage - 1) * pageSize) + 1}–{Math.min(safePage * pageSize, sorted.length)} of {sorted.length}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={safePage === 1}
              aria-label="Previous page"
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <ChevronLeft size={16} aria-hidden="true" />
            </button>
            {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
              let p = i + 1;
              if (totalPages > 7) {
                if (safePage <= 4) p = i + 1;
                else if (safePage >= totalPages - 3) p = totalPages - 6 + i;
                else p = safePage - 3 + i;
              }
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  aria-label={`Page ${p}`}
                  aria-current={p === safePage ? 'page' : undefined}
                  className={`min-w-[32px] h-8 px-2 rounded text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    p === safePage
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-100 text-gray-600'
                  }`}
                >
                  {p}
                </button>
              );
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={safePage === totalPages}
              aria-label="Next page"
              className="p-1 rounded hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <ChevronRight size={16} aria-hidden="true" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
