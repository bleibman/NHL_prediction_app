import type {
  DashboardSummary,
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
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

// Dashboard
export const getDashboardSummary = () =>
  fetchJson<DashboardSummary>("/api/dashboard/summary");

export const getDashboardStandings = () =>
  fetchJson<StandingRow[]>("/api/dashboard/standings");

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
export const getTicketSummary = () =>
  fetchJson<TicketSummary>("/api/tickets/summary");

export const getUpcomingGames = () =>
  fetchJson<UpcomingGame[]>("/api/tickets/upcoming");

export const getPriceTrends = () =>
  fetchJson<PriceTrendPoint[]>("/api/tickets/price-trends");

export const getTeamPrices = () =>
  fetchJson<TeamPrice[]>("/api/tickets/team-prices");

export const getAttendance = (teamAbbrev?: string) =>
  fetchJson<AttendancePoint[]>(
    `/api/tickets/attendance${teamAbbrev ? `?team_abbrev=${teamAbbrev}` : ""}`
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
