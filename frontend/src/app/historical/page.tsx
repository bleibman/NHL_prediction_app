"use client";

import { useEffect, useState } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import PageHeader from "@/components/layout/PageHeader";
import DataTable from "@/components/ui/DataTable";
import Select from "@/components/ui/Select";
import Tabs from "@/components/ui/Tabs";
import HighlightCard from "@/components/cards/HighlightCard";
import PlotlyChart from "@/components/charts/PlotlyChart";
import { formatSeason } from "@/lib/utils";
import {
  getHistoricalSeasons,
  getHistoricalSeason,
  getHistoricalStandings,
  getHistoricalScorers,
  getHistoricalPlayoffs,
  getTeamTrend,
  getTeams,
} from "@/lib/api";
import type { StandingRow, ScorerRow, PlayoffSeriesRow, TeamTrendPoint } from "@/lib/types";

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
  scorerCol.accessor("plus_minus", {
    header: "+/-",
    cell: (info) => {
      const v = info.getValue();
      return v != null ? (v > 0 ? `+${v}` : v) : "\u2014";
    },
  }),
];

const playoffCol = createColumnHelper<PlayoffSeriesRow>();
const playoffColumns = [
  playoffCol.accessor("round_name", { header: "Round" }),
  playoffCol.accessor("matchup", { header: "Matchup" }),
  playoffCol.accessor("score", { header: "Score" }),
  playoffCol.accessor("winner", { header: "Winner", cell: (info) => info.getValue() ?? "\u2014" }),
];

const METRIC_OPTIONS = [
  { value: "points", label: "Points" },
  { value: "point_pct", label: "PTS%" },
  { value: "wins", label: "Wins" },
  { value: "gf_ga_ratio", label: "GF/GA Ratio" },
];

export default function HistoricalPage() {
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number>(0);
  const [tab, setTab] = useState("Team Stats");
  const [standings, setStandings] = useState<StandingRow[]>([]);
  const [scorers, setScorers] = useState<ScorerRow[]>([]);
  const [playoffs, setPlayoffs] = useState<PlayoffSeriesRow[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [selectedTeam, setSelectedTeam] = useState("");
  const [trendData, setTrendData] = useState<TeamTrendPoint[]>([]);
  const [metric, setMetric] = useState("points");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getHistoricalSeasons(), getTeams()]).then(([s, t]) => {
      setSeasons(s);
      setTeams(t);
      if (s.length > 0) setSelectedSeason(s[s.length - 1]);
      if (t.length > 0) setSelectedTeam(t[0]);
      setLoading(false);
    });
  }, []);

  // Load all tab data at once when season changes
  useEffect(() => {
    if (!selectedSeason) return;

    getHistoricalSeason(selectedSeason)
      .then((data) => {
        setStandings(data.standings);
        setScorers(data.scorers);
        setPlayoffs(data.playoffs);
      })
      .catch(() => {
        // Fallback: load individually if consolidated endpoint fails
        Promise.all([
          getHistoricalStandings(selectedSeason),
          getHistoricalScorers(selectedSeason),
          getHistoricalPlayoffs(selectedSeason),
        ]).then(([st, sc, pl]) => {
          setStandings(st);
          setScorers(sc);
          setPlayoffs(pl);
        });
      });
  }, [selectedSeason]);

  useEffect(() => {
    if (selectedTeam) {
      getTeamTrend(selectedTeam).then(setTrendData);
    }
  }, [selectedTeam]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  const champion = playoffs.find((p) => p.round_name === "Stanley Cup Final");
  const trendY = trendData.map((d) => d[metric as keyof TeamTrendPoint] as number);
  const trendX = trendData.map((d) => d.season_display);

  return (
    <>
      <PageHeader title="Historical Data" subtitle="Browse and compare team performance across seasons" />

      <div className="mb-6">
        <Select
          options={seasons.map((s) => ({ value: s.toString(), label: formatSeason(s) }))}
          value={selectedSeason.toString()}
          onChange={(v) => setSelectedSeason(Number(v))}
        />
      </div>

      <Tabs tabs={["Team Stats", "Top Scorers", "Playoff Results"]} activeTab={tab} onChange={setTab} />

      {tab === "Team Stats" && <DataTable columns={standingColumns} data={standings} />}

      {tab === "Top Scorers" && <DataTable columns={scorerColumns} data={scorers} />}

      {tab === "Playoff Results" && (
        <>
          <DataTable columns={playoffColumns} data={playoffs} sortable={false} />
          {champion?.winner && (
            <HighlightCard label="Stanley Cup Champion" icon="\uD83C\uDFC6" title={champion.winner} />
          )}
        </>
      )}

      <hr className="border-border my-8" />

      <h2 className="text-lg font-bold text-text-bright mb-4">Team Trends</h2>
      <div className="flex gap-4 mb-4">
        <Select
          options={teams.map((t) => ({ value: t, label: t }))}
          value={selectedTeam}
          onChange={setSelectedTeam}
        />
        <Select options={METRIC_OPTIONS} value={metric} onChange={setMetric} />
      </div>

      {trendData.length > 0 && (
        <PlotlyChart
          data={[
            {
              x: trendX,
              y: trendY,
              type: "scatter",
              mode: "lines+markers",
              marker: { color: "#1f6feb", size: 6 },
              line: { color: "#1f6feb", width: 2.5 },
            },
          ]}
          layout={{
            xaxis: { title: "", gridcolor: "#21262d", zerolinecolor: "#21262d" },
            yaxis: {
              title: METRIC_OPTIONS.find((m) => m.value === metric)?.label ?? "",
              gridcolor: "#21262d",
              zerolinecolor: "#21262d",
            },
            showlegend: false,
          }}
        />
      )}
    </>
  );
}
