import type {
  DashboardSummary,
  DashboardInit,
  StandingRow,
  ScorerRow,
  PlayoffSeriesRow,
  TeamTrendPoint,
  PredictionRow,
  TicketSummary,
  UpcomingGame,
  PriceTrendPoint,
  TeamPrice,
  AttendancePoint,
  TeamPriceTrendPoint,
  PriceAttendancePoint,
  PriceSpreadPoint,
  TicketFilterOptions,
  HistoricalSeasonData,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "";

// ── Client-side cache ──
const CLIENT_CACHE_TTL = 5 * 60 * 1000; // 5 minutes
const _clientCache = new Map<string, { ts: number; data: unknown }>();

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  // Only cache GET requests (no init body)
  const useCache = !init?.method || init.method === "GET";
  if (useCache) {
    const entry = _clientCache.get(path);
    if (entry && Date.now() - entry.ts < CLIENT_CACHE_TTL) {
      return entry.data as T;
    }
  }

  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  const data: T = await res.json();

  if (useCache) {
    _clientCache.set(path, { ts: Date.now(), data });
  }
  return data;
}

// Dashboard
export const getDashboardInit = () =>
  fetchJson<DashboardInit>("/api/dashboard/init");

export const getDashboardSummary = () =>
  fetchJson<DashboardSummary>("/api/dashboard/summary");

export const getDashboardSeasons = () =>
  fetchJson<number[]>("/api/dashboard/seasons");

export const getDashboardDivisions = () =>
  fetchJson<string[]>("/api/dashboard/divisions");

export const getDashboardStandings = (params?: {
  season_id?: number;
  division?: string;
  team?: string;
}) => {
  const searchParams = new URLSearchParams();
  if (params?.season_id) searchParams.set("season_id", String(params.season_id));
  if (params?.division) searchParams.set("division", params.division);
  if (params?.team) searchParams.set("team", params.team);
  const qs = searchParams.toString();
  return fetchJson<StandingRow[]>(`/api/dashboard/standings${qs ? `?${qs}` : ""}`);
};

export const getDashboardTopScorers = (limit = 10) =>
  fetchJson<ScorerRow[]>(`/api/dashboard/top-scorers?limit=${limit}`);

// Historical
export const getHistoricalSeasons = () =>
  fetchJson<number[]>("/api/historical/seasons");

export const getHistoricalStandings = (seasonId: number) =>
  fetchJson<StandingRow[]>(`/api/historical/standings/${seasonId}`);

export const getHistoricalScorers = (seasonId: number, limit = 50) =>
  fetchJson<ScorerRow[]>(`/api/historical/scorers/${seasonId}?limit=${limit}`);

export const getHistoricalPlayoffs = (seasonId: number) =>
  fetchJson<PlayoffSeriesRow[]>(`/api/historical/playoffs/${seasonId}`);

export const getHistoricalSeason = (seasonId: number) =>
  fetchJson<HistoricalSeasonData>(`/api/historical/season/${seasonId}`);

export const getTeamTrend = (teamAbbrev: string) =>
  fetchJson<TeamTrendPoint[]>(`/api/historical/team-trend/${teamAbbrev}`);

export const getTeams = () =>
  fetchJson<string[]>("/api/historical/teams");

// Predictions
export const getPredictionSeasons = () =>
  fetchJson<number[]>("/api/predictions/seasons");

export const runPredictions = (seasonId: number) =>
  fetchJson<PredictionRow[]>("/api/predictions/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ season_id: seasonId }),
  });

// Tickets
function buildQs(params: Record<string, string | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) sp.set(k, v);
  }
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}

export const getTicketFilterOptions = () =>
  fetchJson<TicketFilterOptions>("/api/tickets/filter-options");

export const getTicketSummary = (params?: { division?: string; team?: string }) =>
  fetchJson<TicketSummary>(`/api/tickets/summary${buildQs({ division: params?.division, team: params?.team })}`);

export const getUpcomingGames = (params?: { division?: string; team?: string }) =>
  fetchJson<UpcomingGame[]>(`/api/tickets/upcoming${buildQs({ division: params?.division, team: params?.team })}`);

export const getPriceTrends = (params?: { division?: string; team?: string }) =>
  fetchJson<PriceTrendPoint[]>(`/api/tickets/price-trends${buildQs({ division: params?.division, team: params?.team })}`);

export const getPriceTrendsByTeam = (params?: { division?: string; team?: string }) =>
  fetchJson<TeamPriceTrendPoint[]>(`/api/tickets/price-trends-by-team${buildQs({ division: params?.division, team: params?.team })}`);

export const getTeamPrices = (params?: { division?: string }) =>
  fetchJson<TeamPrice[]>(`/api/tickets/team-prices${buildQs({ division: params?.division })}`);

export const getPriceSpread = (params?: { division?: string; team?: string }) =>
  fetchJson<PriceSpreadPoint[]>(`/api/tickets/spread${buildQs({ division: params?.division, team: params?.team })}`);

export const getPriceAttendanceCorrelation = () =>
  fetchJson<PriceAttendancePoint[]>("/api/tickets/price-attendance-correlation");

export const getAttendance = (params?: { team_abbrev?: string; season_id?: number; division?: string }) =>
  fetchJson<AttendancePoint[]>(
    `/api/tickets/attendance${buildQs({
      team_abbrev: params?.team_abbrev,
      season_id: params?.season_id ? String(params.season_id) : undefined,
      division: params?.division,
    })}`
  );

export const getAttendanceTeams = () =>
  fetchJson<string[]>("/api/tickets/attendance-teams");

// Refresh
export function startRefresh(
  seasonId: number | null,
  onEvent: (event: Record<string, unknown>) => void
): () => void {
  const controller = new AbortController();

  fetch(`${BASE}/api/refresh/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ season_id: seasonId }),
    signal: controller.signal,
  }).then(async (res) => {
    const reader = res.body?.getReader();
    if (!reader) return;
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            onEvent(JSON.parse(line.slice(6)));
          } catch {}
        }
      }
    }
  }).catch(() => {});

  return () => controller.abort();
}
// force rebuild 1777668760
