"use client";
import { useState, useEffect, useCallback } from "react";
import { useDataSource } from "./data-source-context";
import { mockMiners, mockValidators, mockNetworkStats } from "./mock-data";
import {
  fetchChainSnapshot,
  mapNeuronToMiner,
  mapNeuronToValidator,
  mapSnapshotToNetworkStats,
} from "./taostats";
import type { MinerProfile, ValidatorProfile, NetworkStats } from "./types";

interface NetworkData {
  miners: MinerProfile[];
  validators: ValidatorProfile[];
  networkStats: NetworkStats;
  loading: boolean;
  error: string | null;
  retry: () => void;
}

export function useNetworkData(): NetworkData {
  const { source, setSource } = useDataSource();
  const [miners, setMiners] = useState<MinerProfile[]>(mockMiners);
  const [validators, setValidators] = useState<ValidatorProfile[]>(mockValidators);
  const [networkStats, setNetworkStats] = useState<NetworkStats>(mockNetworkStats);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchCount, setFetchCount] = useState(0);

  const retry = useCallback(() => setFetchCount((c) => c + 1), []);

  useEffect(() => {
    if (source === "mock") {
      setMiners(mockMiners);
      setValidators(mockValidators);
      setNetworkStats(mockNetworkStats);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    (async () => {
      try {
        const snapshot = await fetchChainSnapshot();

        if (cancelled) return;

        const chainMiners = snapshot.neurons
          .filter((n) => n.role === "miner")
          .map((n) => mapNeuronToMiner(n, snapshot.block, snapshot.immunity_period));
        const chainValidators = snapshot.neurons
          .filter((n) => n.role === "validator")
          .map(mapNeuronToValidator);
        const chainStats = mapSnapshotToNetworkStats(snapshot);

        setMiners(chainMiners.length > 0 ? chainMiners : []);
        setValidators(chainValidators.length > 0 ? chainValidators : []);
        setNetworkStats(chainStats);
      } catch (e) {
        if (!cancelled) {
          const message = e instanceof Error ? e.message : "Failed to fetch chain data";
          setError(`${message} — falling back to mock data`);
          setMiners(mockMiners);
          setValidators(mockValidators);
          setNetworkStats(mockNetworkStats);
          setSource("mock");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [source, fetchCount, setSource]);

  return { miners, validators, networkStats, loading, error, retry };
}
