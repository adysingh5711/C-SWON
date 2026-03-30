"use client";
import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

export type DataSource = "mock" | "testnet";

interface DataSourceContextValue {
  source: DataSource;
  setSource: (s: DataSource) => void;
}

const DataSourceContext = createContext<DataSourceContextValue>({
  source: "mock",
  setSource: () => {},
});

const STORAGE_KEY = "cswon-data-source";

export function DataSourceProvider({ children }: { children: ReactNode }) {
  const [source, setSourceState] = useState<DataSource>("mock");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "mock" || stored === "testnet") {
      setSourceState(stored);
    }
    setMounted(true);
  }, []);

  function setSource(s: DataSource) {
    setSourceState(s);
    localStorage.setItem(STORAGE_KEY, s);
  }

  if (!mounted) {
    return <DataSourceContext.Provider value={{ source: "mock", setSource }}>{children}</DataSourceContext.Provider>;
  }

  return (
    <DataSourceContext.Provider value={{ source, setSource }}>
      {children}
    </DataSourceContext.Provider>
  );
}

export function useDataSource() {
  return useContext(DataSourceContext);
}
