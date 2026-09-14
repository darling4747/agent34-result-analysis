import React, { createContext, useCallback, useContext, useState } from 'react';

interface DatasetContextValue {
  refreshKey: number;
  triggerRefresh: () => void;
}

const DatasetContext = createContext<DatasetContextValue>({
  refreshKey: 0,
  triggerRefresh: () => {},
});

export function DatasetProvider({ children }: { children: React.ReactNode }) {
  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);
  return (
    <DatasetContext.Provider value={{ refreshKey, triggerRefresh }}>
      {children}
    </DatasetContext.Provider>
  );
}

export function useDatasetContext() {
  return useContext(DatasetContext);
}
