"use client";

import { useEffect, useState, useCallback } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import PageHeader from "@/components/layout/PageHeader";
import StatCard from "@/components/cards/StatCard";
import DataTable from "@/components/ui/DataTable";
import Select from "@/components/ui/Select";
import {
  getDashboardInit,
  getDashboardSummary,
  getDashboardStandings,
  getDashboardTopScorers,
  getDashboardSeasons,
  getDashboardDivisions,
  getTeams,
} from "@/lib/api";
import { formatSeason } from "@/lib/utils";
import type { DashboardSummary, StandingRow, ScorerRow } from "@/lib/types";

const standingCol = createColumnHelper<StandingRow>();
const standingColumns = [
  standingCol.accessor("team", { header: "Team" }),
  standingCol.accessor("gp", { header: "GP" }),
  standingCol.accessor("w", { header: "W" }),
  standingCol.accessor("l", { header: "L" }),
  standingCol.accessor("otl", { header: "OTL" }),
  standingCol.accessor("pts", { header: "PTS" }),
  standingCol.accessor("pts_pct", { header: "PTS%", cell: (info) => `${info.getValue().toFixed(1)}%` }),
  standingCol.accessor("gf", { header: "GF" }),
  standingCol.accessor("ga", { header: "GA" }),
  standingCol.accessor("pp_pct", { header: "PP%", cell: (info) => `${info.getValue().toFixed(1)}%` }),
  standingCol.accessor("pk_pct", { header: "PK%", cell: (info) => `${info.getValue().toFixed(1)}%` }),
  standingCol.accessor("fo_pct", { header: "FO%", cell: (info) => `${info.getValue().toFixed(1)}%` }),
  standingCol.accessor("sf_pg", { header: "SF/G", cell: (info) => info.getValue().toFixed(1) }),
  standingCol.accessor("sa_pg", { header: "SA/G", cell: (info) => info.getValue().toFixed(1) }),
];

const scorerCol = createColumnHelper<ScorerRow>();
const scorerColumns = [
  scorerCol.accessor("player_name", { header: "Player" }),
  scorerCol.accessor("team", { header: "Team" }),
  scorerCol.accessor("position", { header: "Pos" }),
  scorerCol.accessor("gp", { header: "GP" }),
  scorerCol.accessor("goals", { header: "G" }),
  scorerCol.accessor("assists", { header: "A" }),
  scorerCol.accessor("points", { header: "PTS" }),
];

type FilterMode = "all" | "division" | "team";

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [standings, setStandings] = useState<StandingRow[]>([]);
  const [scorers, setScorers] = useState<ScorerRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [standingsLoading, setStandingsLoading] = useState(false);

  // Filter state
  const [seasons, setSeasons] = useState<number[]>([]);
  const [divisions, setDivisions] = useState<string[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<string>("");
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [selectedDivision, setSelectedDivision] = useState<string>("");
  const [selectedTeam, setSelectedTeam] = useState<string>("");

  // Fetch standings with current filters
  const fetchStandings = useCallback(async (
    seasonId?: string,
    mode?: FilterMode,
    division?: string,
    team?: string,
  ) => {
    setStandingsLoading(true);
    try {
      const params: { season_id?: number; division?: string; team?: string } = {};
      if (seasonId) params.season_id = Number(seasonId);
      if (mode === "division" && division) params.division = division;
      if (mode === "team" && team) params.team = team;
      const data = await getDashboardStandings(params);
      setStandings(data);
    } catch {
      setStandings([]);
    } finally {
      setStandingsLoading(false);
    }
  }, []);

  // Initial load — try consolidated endpoint, fall back to individual calls
  useEffect(() => {
    const applyData = (data: {
      summary: DashboardSummary;
      standings: StandingRow[];
      scorers: ScorerRow[];
      seasons: number[];
      divisions: string[];
      teams: string[];
    }) => {
      setSummary(data.summary);
      setStandings(data.standings);
      setScorers(data.scorers);
      setSeasons(data.seasons);
      setDivisions(data.divisions);
      setTeams(data.teams);
      if (data.seasons.length > 0) setSelectedSeason(String(data.seasons[0]));
      if (data.divisions.length > 0) setSelectedDivision(data.divisions[0]);
      if (data.teams.length > 0) setSelectedTeam(data.teams[0]);
    };

    getDashboardInit()
      .then(applyData)
      .catch(() =>
        Promise.all([
          getDashboardSummary(),
          getDashboardStandings(),
          getDashboardTopScorers(),
          getDashboardSeasons(),
          getDashboardDivisions(),
          getTeams(),
        ]).then(([sum, st, sc, seas, divs, tms]) =>
          applyData({ summary: sum, standings: st, scorers: sc, seasons: seas, divisions: divs, teams: tms })
        )
      )
      .finally(() => setLoading(false));
  }, []);

  // Refetch standings when filters change (skip initial load)
  const handleSeasonChange = (val: string) => {
    setSelectedSeason(val);
    fetchStandings(val, filterMode, selectedDivision, selectedTeam);
  };

  const handleFilterModeChange = (val: string) => {
    const mode = val as FilterMode;
    setFilterMode(mode);
    fetchStandings(selectedSeason, mode, selectedDivision, selectedTeam);
  };

  const handleDivisionChange = (val: string) => {
    setSelectedDivision(val);
    fetchStandings(selectedSeason, "division", val, selectedTeam);
  };

  const handleTeamChange = (val: string) => {
    setSelectedTeam(val);
    fetchStandings(selectedSeason, "team", selectedDivision, val);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  const seasonOptions = seasons.map((s) => ({
    value: String(s),
    label: formatSeason(s),
  }));

  const filterModeOptions = [
    { value: "all", label: "All Teams" },
    { value: "division", label: "By Division" },
    { value: "team", label: "Individual Team" },
  ];

  const divisionOptions = divisions.map((d) => ({
    value: d,
    label: d,
  }));

  const teamOptions = teams.map((t) => ({
    value: t,
    label: t,
  }));

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Standings and team performance overview" />

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Season" value={summary.season_display} />
          <StatCard label="Games Played" value={summary.games_count.toLocaleString()} />
          <StatCard label="Playoff Series" value={summary.playoff_series_count.toString()} />
          <StatCard label="Players Tracked" value={summary.players_count.toLocaleString()} />
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-bold text-text-bright">Standings</h2>
        <div className="flex items-center gap-3">
          {seasonOptions.length > 0 && (
            <Select
              options={seasonOptions}
              value={selectedSeason}
              onChange={handleSeasonChange}
            />
          )}
          <Select
            options={filterModeOptions}
            value={filterMode}
            onChange={handleFilterModeChange}
          />
          {filterMode === "division" && divisionOptions.length > 0 && (
            <Select
              options={divisionOptions}
              value={selectedDivision}
              onChange={handleDivisionChange}
            />
          )}
          {filterMode === "team" && teamOptions.length > 0 && (
            <Select
              options={teamOptions}
              value={selectedTeam}
              onChange={handleTeamChange}
            />
          )}
        </div>
      </div>

      {standingsLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
        </div>
      ) : standings.length > 0 ? (
        <DataTable columns={standingColumns} data={standings} />
      ) : (
        <p className="text-text-muted text-sm py-8 text-center">No standings data available for this selection.</p>
      )}

      <hr className="border-border my-8" />

      <h2 className="text-lg font-bold text-text-bright mb-4">Top 10 Scorers</h2>
      <DataTable columns={scorerColumns} data={scorers} />
    </>
  );
}
