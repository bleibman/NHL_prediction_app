"use client";

import { useEffect, useState, useMemo } from "react";
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
  const [allStandings, setAllStandings] = useState<StandingRow[]>([]);
  const [scorers, setScorers] = useState<ScorerRow[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter state
  const [seasons, setSeasons] = useState<number[]>([]);
  const [divisions, setDivisions] = useState<string[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [teamDivisions, setTeamDivisions] = useState<Record<string, string>>({});
  const [selectedSeason, setSelectedSeason] = useState<string>("");
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [selectedDivision, setSelectedDivision] = useState<string>("");
  const [selectedTeam, setSelectedTeam] = useState<string>("");

  const hasTeamDivisions = Object.keys(teamDivisions).length > 0;

  // Client-side filtered standings
  const filteredStandings = useMemo(() => {
    if (filterMode === "division" && selectedDivision && hasTeamDivisions) {
      return allStandings.filter((row) => teamDivisions[row.team] === selectedDivision);
    }
    if (filterMode === "team" && selectedTeam) {
      return allStandings.filter((row) => row.team === selectedTeam);
    }
    return allStandings;
  }, [allStandings, filterMode, selectedDivision, selectedTeam, teamDivisions, hasTeamDivisions]);

  // Initial load — try consolidated endpoint, fall back to individual calls
  useEffect(() => {
    const applyData = (data: {
      summary: DashboardSummary;
      standings: StandingRow[];
      scorers: ScorerRow[];
      seasons: number[];
      divisions: string[];
      teams: string[];
      team_divisions?: Record<string, string>;
    }) => {
      setSummary(data.summary);
      setAllStandings(data.standings);
      setScorers(data.scorers);
      setSeasons(data.seasons);
      setDivisions(data.divisions);
      setTeams(data.teams);
      if (data.team_divisions) setTeamDivisions(data.team_divisions);
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

  // Season change: fetch full unfiltered standings for the new season
  const handleSeasonChange = async (val: string) => {
    setSelectedSeason(val);
    try {
      const data = await getDashboardStandings({ season_id: Number(val) });
      setAllStandings(data);
    } catch {
      setAllStandings([]);
    }
  };

  const handleFilterModeChange = (val: string) => {
    setFilterMode(val as FilterMode);
  };

  const handleDivisionChange = async (val: string) => {
    setSelectedDivision(val);
    // Fallback: if team_divisions mapping is unavailable, fetch from API
    if (!hasTeamDivisions) {
      try {
        const data = await getDashboardStandings({
          season_id: Number(selectedSeason),
          division: val,
        });
        setAllStandings(data);
      } catch {
        // keep current standings
      }
    }
  };

  const handleTeamChange = (val: string) => {
    setSelectedTeam(val);
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

      {filteredStandings.length > 0 ? (
        <DataTable columns={standingColumns} data={filteredStandings} />
      ) : (
        <p className="text-text-muted text-sm py-8 text-center">No standings data available for this selection.</p>
      )}

      <hr className="border-border my-8" />

      <h2 className="text-lg font-bold text-text-bright mb-4">Top 10 Scorers</h2>
      <DataTable columns={scorerColumns} data={scorers} />
    </>
  );
}
