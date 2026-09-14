import { useEffect, useRef, useState } from 'react';
import { useDatasetContext } from '@/contexts/DatasetContext';
import {
  getCorrelation, getCourses, getFaculty, getGradeDistribution,
  getHistorical, getInterventionSummary, getInterventions,
  getMeritList, getNarrative, getSections, getSummary,
} from '@/api/analysisApi';
import type {
  AnalyticalNarrative, CorrelationResult, CourseMetrics, FacultyMetrics,
  GradeDistributionItem, HistoricalComparison, InterventionCourse,
  InterventionSummary, MeritEntry, SectionMetrics, ResultSummary,
} from '@/types/analysis';
import type { ResultFilters } from '@/types/result';
import { ApiError } from '@/api/client';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  isNetworkError: boolean;
}

type Setter<T> = React.Dispatch<React.SetStateAction<AsyncState<T>>>;

async function runFetch<T>(
  fetcher: (f: ResultFilters) => Promise<T>,
  filters: ResultFilters,
  set: Setter<T>,
  signal: AbortSignal,
) {
  try {
    const data = await fetcher(filters);
    if (signal.aborted) return;
    set({ data, loading: false, error: null, isNetworkError: false });
  } catch (err) {
    if (signal.aborted) return;
    if (err instanceof ApiError) {
      set({ data: null, loading: false, error: err.message, isNetworkError: err.isNetworkError });
    } else {
      set({ data: null, loading: false, error: 'An unexpected error occurred.', isNetworkError: false });
    }
  }
}

function useApiData<T>(
  fetcher: (filters: ResultFilters) => Promise<T>,
  filters: ResultFilters,
) {
  const [state, setState] = useState<AsyncState<T>>({ data: null, loading: true, error: null, isNetworkError: false });
  const abortRef = useRef<AbortController | null>(null);
  const { refreshKey } = useDatasetContext();
  const filtersKey = JSON.stringify(filters);

  useEffect(() => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    void runFetch(fetcher, filters, setState, ctrl.signal);
    return () => ctrl.abort();
  }, [filtersKey, refreshKey]);

  const retry = () => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setState({ data: null, loading: true, error: null, isNetworkError: false });
    void runFetch(fetcher, filters, setState, ctrl.signal);
  };

  return { ...state, retry };
}

export function useSummary(f: ResultFilters)            { return useApiData<ResultSummary>(getSummary, f); }
export function useGradeDistribution(f: ResultFilters)  { return useApiData<GradeDistributionItem[]>(getGradeDistribution, f); }
export function useCourses(f: ResultFilters)             { return useApiData<CourseMetrics[]>(getCourses, f); }
export function useSections(f: ResultFilters)            { return useApiData<SectionMetrics[]>(getSections, f); }
export function useFaculty(f: ResultFilters)             { return useApiData<FacultyMetrics[]>(getFaculty, f); }
export function useMeritList(f: ResultFilters)           { return useApiData<MeritEntry[]>(getMeritList, f); }
export function useCorrelation(f: ResultFilters)         { return useApiData<CorrelationResult[]>(getCorrelation, f); }
export function useHistorical(f: ResultFilters)          { return useApiData<HistoricalComparison[]>(getHistorical, f); }
export function useInterventions(f: ResultFilters)       { return useApiData<InterventionCourse[]>(getInterventions, f); }
export function useInterventionSummary(f: ResultFilters) { return useApiData<InterventionSummary>(getInterventionSummary, f); }
export function useNarrative(f: ResultFilters)           { return useApiData<AnalyticalNarrative>(getNarrative, f); }

export function useDashboardData(filters: ResultFilters) {
  const summary       = useSummary(filters);
  const grades        = useGradeDistribution(filters);
  const courses       = useCourses(filters);
  const sections      = useSections(filters);
  const interventions = useInterventions(filters);
  const narrative     = useNarrative(filters);
  const loading = summary.loading || grades.loading || courses.loading;
  return { summary, grades, courses, sections, interventions, narrative, loading };
}