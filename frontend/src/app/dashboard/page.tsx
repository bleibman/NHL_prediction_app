"use client";

import { useEffect, useState } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import PageHeader from "@/components/layout/PageHeader";
import StatCard from "@/components/cards/StatCard";
import DataTable from "@/components/ui/DataTable";
import { getDashboardSummary, getDashboardStandings, getDashboardTopScorers } from "@/lib/api";
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

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [standings, setStandings] = useState<StandingRow[]>([]);
  const [scorers, setScorers] = useState<ScorerRow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getDashboardSummary(),
      getDashboardStandings(),
      getDashboardTopScorers(),
    ])
      .then(([s, st, sc]) => {
        setSummary(s);
        setStandings(st);
        setScorers(sc);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Current standings and team performance overview" />

      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Season" value={summary.season_display} />
          <StatCard label="Games Played" value={summary.games_count.toLocaleString()} />
          <StatCard label="Playoff Series" value={summary.playoff_series_count.toString()} />
          <StatCard label="Players Tracked" value={summary.players_count.toLocaleString()} />
        </div>
      )}

      <h2 className="text-lg font-bold text-text-bright mb-4">Standings</h2>
      <DataTable columns={standingColumns} data={standings} />

      <hr className="border-border my-8" />

      <h2 className="text-lg font-bold text-text-bright mb-4">Top 10 Scorers</h2>
      <DataTable columns={scorerColumns} data={scorers} />
    </>
  );
}
