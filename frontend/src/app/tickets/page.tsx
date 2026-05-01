"use client";

import { useEffect, useState, useCallback } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import PageHeader from "@/components/layout/PageHeader";
import StatCard from "@/components/cards/StatCard";
import InfoBox from "@/components/cards/InfoBox";
import DataTable from "@/components/ui/DataTable";
import Select from "@/components/ui/Select";
import PlotlyChart from "@/components/charts/PlotlyChart";
import {
  getTicketSummary,
  getUpcomingGames,
  getPriceTrends,
  getPriceTrendsByTeam,
  getTeamPrices,
  getPriceSpread,
  getPriceAttendanceCorrelation,
  getAttendance,
  getAttendanceTeams,
  getTicketFilterOptions,
} from "@/lib/api";
import type {
  TicketSummary,
  UpcomingGame,
  PriceTrendPoint,
  TeamPrice,
  AttendancePoint,
  TeamPriceTrendPoint,
  PriceAttendancePoint,
  PriceSpreadPoint,
} from "@/lib/types";

const gameCol = createColumnHelper<UpcomingGame>();
const gameColumns = [
  gameCol.accessor("date", { header: "Date" }),
  gameCol.accessor("home_team", { header: "Home" }),
  gameCol.accessor("away_team", { header: "Away" }),
  gameCol.accessor("venue_name", {
    header: "Venue",
    cell: (info) => info.getValue() ?? "\u2014",
  }),
  gameCol.accessor("venue_city", {
    header: "City",
    cell: (info) => info.getValue() ?? "\u2014",
  }),
  gameCol.accessor("avg_price", {
    header: "Avg $",
    cell: (info) => (info.getValue() != null ? `$${info.getValue()}` : "\u2014"),
  }),
  gameCol.accessor("low_price", {
    header: "Low $",
    cell: (info) => (info.getValue() != null ? `$${info.getValue()}` : "\u2014"),
  }),
  gameCol.accessor("high_price", {
    header: "High $",
    cell: (info) => (info.getValue() != null ? `$${info.getValue()}` : "\u2014"),
  }),
  gameCol.accessor("spread", {
    header: "Spread",
    cell: (info) => (info.getValue() != null ? `$${info.getValue()}` : "\u2014"),
  }),
  gameCol.accessor("listings", {
    header: "Listings",
    cell: (info) => info.getValue()?.toLocaleString() ?? "\u2014",
  }),
];

type FilterMode = "all" | "division" | "team";

const TEAM_COLORS = [
  "#1f6feb", "#58a6ff", "#f78166", "#7ee787", "#d2a8ff",
  "#ff7b72", "#79c0ff", "#ffa657", "#56d4dd", "#e6edf3",
  "#b392f0", "#ffdf5d", "#85e89d", "#f692ce", "#9ecbff",
  "#dbedff",
];

export default function TicketsPage() {
  const [summary, setSummary] = useState<TicketSummary | null>(null);
  const [upcoming, setUpcoming] = useState<UpcomingGame[]>([]);
  const [trends, setTrends] = useState<PriceTrendPoint[]>([]);
  const [teamTrends, setTeamTrends] = useState<TeamPriceTrendPoint[]>([]);
  const [teamPrices, setTeamPrices] = useState<TeamPrice[]>([]);
  const [spreadData, setSpreadData] = useState<PriceSpreadPoint[]>([]);
  const [correlation, setCorrelation] = useState<PriceAttendancePoint[]>([]);
  const [attTeams, setAttTeams] = useState<string[]>([]);
  const [selectedAttTeam, setSelectedAttTeam] = useState("");
  const [attendance, setAttendance] = useState<AttendancePoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(false);

  // Filter state
  const [divisions, setDivisions] = useState<string[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [selectedDivision, setSelectedDivision] = useState("");
  const [selectedTeam, setSelectedTeam] = useState("");

  const getFilterParams = useCallback(
    (mode?: FilterMode, div?: string, tm?: string) => {
      const m = mode ?? filterMode;
      const d = div ?? selectedDivision;
      const t = tm ?? selectedTeam;
      const params: { division?: string; team?: string } = {};
      if (m === "division" && d) params.division = d;
      if (m === "team" && t) params.team = t;
      return params;
    },
    [filterMode, selectedDivision, selectedTeam]
  );

  const fetchFilteredData = useCallback(
    async (mode?: FilterMode, div?: string, tm?: string) => {
      setDataLoading(true);
      const params = getFilterParams(mode, div, tm);
      try {
        const [s, u, t, tt, tp, sp] = await Promise.all([
          getTicketSummary(params),
          getUpcomingGames(params),
          getPriceTrends(params),
          getPriceTrendsByTeam(params),
          getTeamPrices({ division: params.division }),
          getPriceSpread(params),
        ]);
        setSummary(s);
        setUpcoming(u);
        setTrends(t);
        setTeamTrends(tt);
        setTeamPrices(tp);
        setSpreadData(sp);
      } catch {
        // keep existing data
      } finally {
        setDataLoading(false);
      }
    },
    [getFilterParams]
  );

  // Initial load
  useEffect(() => {
    Promise.all([
      getTicketSummary(),
      getUpcomingGames(),
      getPriceTrends(),
      getPriceTrendsByTeam(),
      getTeamPrices(),
      getPriceSpread(),
      getPriceAttendanceCorrelation(),
      getAttendanceTeams(),
      getTicketFilterOptions(),
    ])
      .then(([s, u, t, tt, tp, sp, corr, at, fo]) => {
        setSummary(s);
        setUpcoming(u);
        setTrends(t);
        setTeamTrends(tt);
        setTeamPrices(tp);
        setSpreadData(sp);
        setCorrelation(corr);
        setAttTeams(at);
        setDivisions(fo.divisions);
        setTeams(fo.teams);
        if (fo.divisions.length > 0) setSelectedDivision(fo.divisions[0]);
        if (fo.teams.length > 0) setSelectedTeam(fo.teams[0]);
        if (at.length > 0) setSelectedAttTeam(at[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedAttTeam) {
      getAttendance({ team_abbrev: selectedAttTeam }).then(setAttendance);
    }
  }, [selectedAttTeam]);

  const handleFilterModeChange = (val: string) => {
    const mode = val as FilterMode;
    setFilterMode(mode);
    fetchFilteredData(mode, selectedDivision, selectedTeam);
  };

  const handleDivisionChange = (val: string) => {
    setSelectedDivision(val);
    fetchFilteredData("division", val, selectedTeam);
  };

  const handleTeamChange = (val: string) => {
    setSelectedTeam(val);
    fetchFilteredData("team", selectedDivision, val);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  const hasTicketData = summary && summary.games_tracked > 0;

  // Build price trends chart traces
  const showTeamLines = filterMode !== "all" && teamTrends.length > 0;
  const trendTraces = (() => {
    if (showTeamLines) {
      const byTeam = new Map<string, TeamPriceTrendPoint[]>();
      for (const pt of teamTrends) {
        const arr = byTeam.get(pt.team) ?? [];
        arr.push(pt);
        byTeam.set(pt.team, arr);
      }
      const entries = Array.from(byTeam.entries());
      const traces: Plotly.Data[] = entries.map(([team, points], i) => {
        const sorted = points.sort((a, b) => a.days_until_game - b.days_until_game);
        return {
          x: sorted.map((p) => p.days_until_game),
          y: sorted.map((p) => p.average_price),
          type: "scatter" as const,
          mode: "lines+markers" as const,
          name: team,
          marker: { color: TEAM_COLORS[i % TEAM_COLORS.length], size: 5 },
          line: { color: TEAM_COLORS[i % TEAM_COLORS.length], width: 2 },
        };
      });
      // League average reference line
      if (trends.length >= 2) {
        traces.push({
          x: trends.map((t) => t.days_until_game),
          y: trends.map((t) => t.average_price),
          type: "scatter" as const,
          mode: "lines" as const,
          name: "League Avg",
          line: { color: "#484f58", width: 2, dash: "dash" },
        });
      }
      return traces;
    }
    return [
      {
        x: trends.map((t) => t.days_until_game),
        y: trends.map((t) => t.average_price),
        type: "scatter" as const,
        mode: "lines+markers" as const,
        marker: { color: "#1f6feb", size: 6 },
        line: { color: "#1f6feb", width: 2.5 },
      },
    ];
  })();

  const filterModeOptions = [
    { value: "all", label: "All Teams" },
    { value: "division", label: "By Division" },
    { value: "team", label: "Individual Team" },
  ];

  const divisionOptions = divisions.map((d) => ({ value: d, label: d }));
  const teamOptions = teams.map((t) => ({ value: t, label: t }));

  return (
    <>
      <PageHeader title="Ticket Analytics" subtitle="NHL ticket prices, trends, and attendance data" />

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
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
        {dataLoading && (
          <div className="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full" />
        )}
      </div>

      {!hasTicketData ? (
        <InfoBox text="No ticket data available yet. Set SEATGEEK_CLIENT_ID in your environment and run Data Refresh to fetch ticket prices." />
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
            <StatCard
              label="Avg Ticket Price"
              value={summary.avg_price != null ? `$${Math.round(summary.avg_price)}` : "N/A"}
            />
            <StatCard
              label="Lowest Available"
              value={summary.lowest_price != null ? `$${summary.lowest_price}` : "N/A"}
            />
            <StatCard
              label="Avg Spread"
              value={summary.avg_spread != null ? `$${Math.round(summary.avg_spread)}` : "N/A"}
            />
            <StatCard
              label="Total Listings"
              value={summary.total_listings != null ? summary.total_listings.toLocaleString() : "N/A"}
            />
            <StatCard
              label="Games Tracked"
              value={summary.games_tracked.toString()}
              sub={summary.snapshot_date ? `as of ${summary.snapshot_date}` : undefined}
            />
          </div>

          {/* Upcoming Games */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Upcoming Games</h2>
          <DataTable columns={gameColumns} data={upcoming} />

          <hr className="border-border my-8" />

          {/* Price Trends */}
          <h2 className="text-lg font-bold text-text-bright mb-4">
            Price Trends {filterMode !== "all" ? "(by Team)" : ""}
          </h2>
          {(trends.length >= 2 || (showTeamLines && teamTrends.length > 0)) ? (
            <PlotlyChart
              data={trendTraces}
              layout={{
                xaxis: {
                  title: "Days Until Game",
                  autorange: "reversed",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                },
                yaxis: {
                  title: "Average Price ($)",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                },
                showlegend: showTeamLines,
                legend: { font: { color: "#c9d1d9" } },
              }}
            />
          ) : (
            <InfoBox text="Price trend analysis requires at least 2 days of snapshot data. Run the daily ticket fetch to accumulate history." />
          )}

          <hr className="border-border my-8" />

          {/* Price Spread */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Price Spread by Team</h2>
          {spreadData.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: spreadData.map((s) => s.avg_spread),
                  y: spreadData.map((s) => s.team),
                  type: "bar",
                  orientation: "h",
                  marker: {
                    color: spreadData.map((s) => s.avg_spread),
                    colorscale: [
                      [0, "#238636"],
                      [0.5, "#d29922"],
                      [1, "#da3633"],
                    ],
                  },
                  text: spreadData.map(
                    (s) => `$${Math.round(s.avg_spread)} (Low: $${Math.round(s.avg_lowest)} / High: $${Math.round(s.avg_highest)})`
                  ),
                  textposition: "outside",
                  textfont: { color: "#c9d1d9", size: 11 },
                  hovertemplate:
                    "<b>%{y}</b><br>Spread: $%{x:.0f}<br>Avg Low: $%{customdata[0]:.0f}<br>Avg High: $%{customdata[1]:.0f}<br>Listings: %{customdata[2]}<extra></extra>",
                  customdata: spreadData.map((s) => [s.avg_lowest, s.avg_highest, s.listing_count]),
                },
              ]}
              layout={{
                xaxis: {
                  title: "Average Price Spread ($)",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                },
                yaxis: { title: "", gridcolor: "#21262d", zerolinecolor: "#21262d" },
                showlegend: false,
              }}
              height={Math.max(400, spreadData.length * 28)}
            />
          ) : (
            <InfoBox text="No spread data available for current filter." />
          )}

          <hr className="border-border my-8" />

          {/* Team Price Comparison */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Average Price by Team</h2>
          {teamPrices.length > 0 && (
            <PlotlyChart
              data={[
                {
                  x: teamPrices.map((t) => t.average_price),
                  y: teamPrices.map((t) => t.team),
                  type: "bar",
                  orientation: "h",
                  marker: {
                    color: teamPrices.map((t) => t.average_price),
                    colorscale: [
                      [0, "#21262d"],
                      [0.5, "#1f6feb"],
                      [1, "#58a6ff"],
                    ],
                  },
                  text: teamPrices.map((t) => `$${Math.round(t.average_price)}`),
                  textposition: "outside",
                  textfont: { color: "#c9d1d9", size: 12 },
                  hovertemplate: teamPrices.map(
                    (t) =>
                      `<b>${t.team}</b><br>Avg: $${Math.round(t.average_price)}<br>Low: ${t.lowest_price != null ? "$" + Math.round(t.lowest_price) : "N/A"}<br>High: ${t.highest_price != null ? "$" + Math.round(t.highest_price) : "N/A"}<extra></extra>`
                  ),
                },
              ]}
              layout={{
                xaxis: {
                  title: "Average Ticket Price ($)",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                },
                yaxis: { title: "", gridcolor: "#21262d", zerolinecolor: "#21262d" },
                showlegend: false,
              }}
              height={Math.max(400, teamPrices.length * 28)}
            />
          )}

          <hr className="border-border my-8" />

          {/* Price vs Attendance Correlation */}
          <h2 className="text-lg font-bold text-text-bright mb-4">
            Price vs Attendance (Capacity Utilization)
          </h2>
          {correlation.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: correlation.map((c) => c.avg_ticket_price),
                  y: correlation.map((c) => c.utilization_pct ?? c.avg_attendance),
                  text: correlation.map((c) => c.team),
                  type: "scatter",
                  mode: "markers+text",
                  textposition: "top center",
                  textfont: { color: "#c9d1d9", size: 10 },
                  marker: {
                    color: "#1f6feb",
                    size: 12,
                    opacity: 0.8,
                  },
                  hovertemplate: correlation.map(
                    (c) =>
                      `<b>${c.team}</b><br>Avg Price: $${Math.round(c.avg_ticket_price)}<br>Avg Attendance: ${Math.round(c.avg_attendance).toLocaleString()}<br>Capacity: ${c.capacity?.toLocaleString() ?? "N/A"}<br>Utilization: ${c.utilization_pct != null ? c.utilization_pct + "%" : "N/A"}<extra></extra>`
                  ),
                },
              ]}
              layout={{
                xaxis: {
                  title: "Average Ticket Price ($)",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                },
                yaxis: {
                  title: correlation.some((c) => c.utilization_pct != null)
                    ? "Capacity Utilization (%)"
                    : "Average Attendance",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                },
                showlegend: false,
              }}
            />
          ) : (
            <InfoBox text="No correlation data available. Requires both ticket snapshot data and historical attendance data." />
          )}
        </>
      )}

      <hr className="border-border my-8" />

      {/* Historical Attendance */}
      <h2 className="text-lg font-bold text-text-bright mb-4">Historical Attendance</h2>
      {attTeams.length > 0 ? (
        <>
          <div className="mb-4">
            <Select
              options={attTeams.map((t) => ({ value: t, label: t }))}
              value={selectedAttTeam}
              onChange={setSelectedAttTeam}
            />
          </div>
          {attendance.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: attendance.map((a) => a.season_display),
                  y: attendance.map((a) => a.avg_attendance),
                  type: "bar",
                  marker: { color: "#1f6feb" },
                },
              ]}
              layout={{
                xaxis: { title: "", gridcolor: "#21262d", zerolinecolor: "#21262d" },
                yaxis: {
                  title: "Average Attendance",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                },
                showlegend: false,
              }}
            />
          ) : (
            <InfoBox text={`No attendance data for ${selectedAttTeam}.`} />
          )}
        </>
      ) : (
        <InfoBox text="No attendance data imported yet. Download the Kaggle NHL Games CSV and run: python scripts/import_attendance.py data/nhl_games.csv" />
      )}
    </>
  );
}
