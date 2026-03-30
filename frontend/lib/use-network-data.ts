"use client";
import { useState, useEffect, useCallback } from "react";
import { useDataSource } from "./data-source-context";
import { mockMiners, mockValidators, mockNetworkStats } from "./mock-data";
import {
  fetchMetagraph,
  fetchSubnetInfo,
  mapNeuronToMiner,
  mapNeuronToValidator,
  mapSubnetToNetworkStats,
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
  const { source } = useDataSource();
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
        const [neurons, subnet] = await Promise.all([
          fetchMetagraph(),
          fetchSubnetInfo(),
        ]);

        if (cancelled) return;

        const chainMiners = neurons
          .filter((n) => !n.validator_permit)
          .map(mapNeuronToMiner);
        const chainValidators = neurons
          .filter((n) => n.validator_permit)
          .map(mapNeuronToValidator);
        const chainStats = mapSubnetToNetworkStats(subnet, neurons);

        setMiners(chainMiners.length > 0 ? chainMiners : []);
        setValidators(chainValidators.length > 0 ? chainValidators : []);
        setNetworkStats(chainStats);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Failed to fetch testnet data");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [source, fetchCount]);

  return { miners, validators, networkStats, loading, error, retry };
}
