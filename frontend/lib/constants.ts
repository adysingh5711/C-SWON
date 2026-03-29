// Design tokens for C-SWON dark network operations interface
export const colors = {
  canvas: "#0a0e17",
  surface0: "#0f1420",
  surface1: "#141a2a",
  surface2: "#1a2235",
  surface3: "#212b40",
  ink: "#e8edf5",
  inkSecondary: "#8a94a8",
  inkTertiary: "#5a6478",
  inkMuted: "#3d4658",
  border: "rgba(138, 148, 168, 0.12)",
  borderEmphasis: "rgba(138, 148, 168, 0.25)",
  borderFocus: "rgba(0, 212, 170, 0.5)",
  teal: "#00d4aa",
  tealMuted: "rgba(0, 212, 170, 0.15)",
  tealDim: "#00a885",
  gold: "#f0b429",
  goldMuted: "rgba(240, 180, 41, 0.15)",
  success: "#22c55e",
  successMuted: "rgba(34, 197, 94, 0.15)",
  warning: "#eab308",
  warningMuted: "rgba(234, 179, 8, 0.15)",
  error: "#ef4444",
  errorMuted: "rgba(239, 68, 68, 0.15)",
} as const;

export const scoring = {
  weights: { success: 0.50, cost: 0.25, latency: 0.15, reliability: 0.10 },
  successGate: 0.70,
  windowSize: 100,
  maxMinerWeight: 0.15,
  warmupThreshold: 20,
} as const;

export const network = {
  tempo: 360,
  execSupportMin: 30,
  queryTimeout: 9,
  immunityPeriod: 5000,
} as const;
