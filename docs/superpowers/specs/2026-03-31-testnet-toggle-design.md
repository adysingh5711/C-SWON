# Testnet/Mock Data Toggle — Design Spec

**Date:** 2026-03-31
**Scope:** Frontend only — Dashboard, Explorer, Submit Task pages
**Subnet:** netuid 26 (testnet)

---

## Goal

Add a per-page toggle switch that lets users switch between mock demo data and live testnet chain data fetched from the Taostats API. This allows Ideathon evaluators to verify the subnet is live on-chain directly from the frontend.

---

## Architecture

### 1. Data Source Context (`lib/data-source-context.tsx`)

React Context + localStorage for persistent state.

```typescript
type DataSource = "mock" | "testnet";

interface DataSourceContextValue {
  source: DataSource;
  setSource: (s: DataSource) => void;
}
```

- Provider wraps the app in `layout.tsx`
- Reads initial value from `localStorage` key `cswon-data-source`, defaults to `"mock"`
- Writes to `localStorage` on every change
- `useDataSource()` hook exposes `{ source, setSource }`

### 2. Taostats API Client (`lib/taostats.ts`)

Two fetch functions targeting the public Taostats REST API:

- `fetchMetagraph(netuid: number, network: "test")` — returns per-UID data (stake, hotkey, coldkey, incentive, dividends, emission, active status)
- `fetchSubnetInfo(netuid: number, network: "test")` — returns subnet metadata (tempo, block height, emission rate, registration cost, owner)

**Endpoint pattern:**
```
GET https://api.taostats.io/api/metagraph/latest/v1?netuid=26&network=test
GET https://api.taostats.io/api/subnet/latest/v1?netuid=26&network=test
```

**Error handling:**
- On fetch failure: show an inline error banner ("Failed to load testnet data") and offer a retry button
- Do not auto-fall back to mock — the user explicitly chose testnet, so make the failure visible

**Caching:**
- Cache responses for 60 seconds using a simple timestamp check (no library needed)
- Prevents re-fetching on every page navigation within the same session

### 3. Data Mapping (`lib/taostats-mapper.ts`)

Maps Taostats API responses to existing frontend types (`MinerProfile`, `ValidatorProfile`, `NetworkStats`).

| Taostats Field | Frontend Type Field | Notes |
|---|---|---|
| `uid` | `MinerProfile.uid` | Direct |
| `hotkey` | `MinerProfile.hotkey` | Direct |
| `coldkey` | `MinerProfile.coldkey` | Direct |
| `stake` | `MinerProfile.stake` | Float, in alpha (ב) |
| `incentive` | `MinerProfile.scores.composite` | Normalized 0-1 |
| `dividends` | `ValidatorProfile.dividends` | Normalized 0-1 |
| `emission` | `MinerProfile.emission` | Per-tempo emission |
| `active` | Used to filter serving UIDs | Boolean |
| `validator_permit` | Used to classify UID as validator vs miner | Boolean |

**Fields unavailable from chain:**
- `scores.success`, `scores.cost`, `scores.latency`, `scores.reliability` — these are C-SWON-internal scoring dimensions not stored on-chain
- `tasks_seen`, `weight`, `weight_capped` — internal validator state
- When in testnet mode, these columns show "—" with a tooltip "Available in mock mode"

### 4. Data Hook (`lib/use-network-data.ts`)

A custom hook that returns the appropriate data based on the current data source:

```typescript
function useNetworkData(): {
  miners: MinerProfile[];
  validators: ValidatorProfile[];
  networkStats: NetworkStats;
  loading: boolean;
  error: string | null;
  retry: () => void;
}
```

- When `source === "mock"`: returns imported mock data immediately (no loading state)
- When `source === "testnet"`: fetches from Taostats, returns loading/error states
- Uses the 60-second cache from the API client

### 5. Toggle Component (`components/data-source-toggle.tsx`)

A small pill-shaped toggle rendered at the top-right of each page section.

**Props:**
```typescript
interface DataSourceToggleProps {
  mode: "enabled" | "coming-soon";
}
```

**Behavior:**
- `"enabled"` (Dashboard, Explorer): functional toggle between Mock and Testnet
- `"coming-soon"` (Submit Task): mock side active, testnet side greyed out with "Coming Soon" text on hover/click

**Visual:**
- Compact pill: `Mock ●━○ Testnet` or `Mock ○━● Testnet`
- Uses existing design tokens (teal accent for active state)
- Active side gets `bg-[--color-teal]/15 text-[--color-teal]`
- Inactive side gets `text-[--color-ink-tertiary]`
- Coming-soon side gets `opacity-50 cursor-not-allowed` with tooltip

### 6. Page Changes

**Dashboard (`app/dashboard/page.tsx`):**
- Replace direct mock imports with `useNetworkData()` hook
- Add `<DataSourceToggle mode="enabled" />` below the page heading
- Show loading skeleton (4 stat card placeholders + table placeholder) while fetching
- In testnet mode, hide columns that require C-SWON-internal data (success/cost/latency/reliability breakdown) and show simplified leaderboard (UID, hotkey, stake, incentive, emission)

**Explorer (`app/explorer/page.tsx`):**
- Replace mock profile data with `useNetworkData()` hook filtered by UID
- Add `<DataSourceToggle mode="enabled" />` below the page heading
- In testnet mode, show chain-available fields only (stake, incentive, emission, registration block)
- Score breakdown gauges show "Chain data — breakdown unavailable" in testnet mode

**Submit Task (`app/submit/page.tsx`):**
- Add `<DataSourceToggle mode="coming-soon" />` below the page heading
- No data source changes — continues using mock simulation
- Testnet side of toggle shows "Coming Soon" tooltip

**Home (`app/page.tsx`):**
- No toggle. Static marketing page.

---

## What Is NOT In Scope

- Building a validator REST API for real task submission
- Websocket/real-time data updates
- Historical data or time-series charts from Taostats
- Authentication or rate limiting for the Taostats API (public endpoints)
- Changes to the Python backend

---

## File Summary

| File | Action | Purpose |
|---|---|---|
| `lib/data-source-context.tsx` | New | React Context + localStorage persistence |
| `lib/taostats.ts` | New | Taostats API client with caching |
| `lib/taostats-mapper.ts` | New | Map API responses to frontend types |
| `lib/use-network-data.ts` | New | Hook returning mock or live data |
| `components/data-source-toggle.tsx` | New | Toggle pill component |
| `app/layout.tsx` | Edit | Wrap with DataSourceProvider |
| `app/dashboard/page.tsx` | Edit | Use hook + toggle, loading states |
| `app/explorer/page.tsx` | Edit | Use hook + toggle, loading states |
| `app/submit/page.tsx` | Edit | Add coming-soon toggle |
