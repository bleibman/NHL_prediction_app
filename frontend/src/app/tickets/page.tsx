"use client";

import { useEffect, useState, useMemo } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import PageHeader from "@/components/layout/PageHeader";
import StatCard from "@/components/cards/StatCard";
import InfoBox from "@/components/cards/InfoBox";
import DataTable from "@/components/ui/DataTable";
import Select from "@/components/ui/Select";
import PlotlyChart from "@/components/charts/PlotlyChart";
import {
  getTicketsInit,
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
  PerformancePricePoint,
  AttendanceOverviewPoint,
  AdvancedAttendancePoint,
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
  // Full unfiltered data from /init
  const [allUpcoming, setAllUpcoming] = useState<UpcomingGame[]>([]);
  const [allTeamPrices, setAllTeamPrices] = useState<TeamPrice[]>([]);
  const [allSpread, setAllSpread] = useState<PriceSpreadPoint[]>([]);
  const [allTeamTrends, setAllTeamTrends] = useState<TeamPriceTrendPoint[]>([]);
  const [allPriceTrends, setAllPriceTrends] = useState<PriceTrendPoint[]>([]);
  const [correlation, setCorrelation] = useState<PriceAttendancePoint[]>([]);
  const [attTeams, setAttTeams] = useState<string[]>([]);
  const [teamDivisions, setTeamDivisions] = useState<Record<string, string>>({});

  // New Kaggle-derived data
  const [performancePrice, setPerformancePrice] = useState<PerformancePricePoint[]>([]);
  const [attendanceOverview, setAttendanceOverview] = useState<AttendanceOverviewPoint[]>([]);
  const [advancedAttendance, setAdvancedAttendance] = useState<AdvancedAttendancePoint[]>([]);

  // Attendance (separate call per team)
  const [selectedAttTeam, setSelectedAttTeam] = useState("");
  const [attendance, setAttendance] = useState<AttendancePoint[]>([]);

  const [loading, setLoading] = useState(true);

  // Filter state
  const [divisions, setDivisions] = useState<string[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [selectedDivision, setSelectedDivision] = useState("");
  const [selectedTeam, setSelectedTeam] = useState("");

  // Initial load — single API call with fallback
  useEffect(() => {
    getTicketsInit()
      .then((data) => {
        setAllUpcoming(data.upcoming);
        setAllTeamPrices(data.team_prices);
        setAllSpread(data.spread);
        setAllTeamTrends(data.team_trends);
        setAllPriceTrends(data.price_trends);
        setCorrelation(data.correlation);
        setAttTeams(data.attendance_teams);
        setTeamDivisions(data.team_divisions);
        setDivisions(data.filter_options.divisions);
        setTeams(data.filter_options.teams);
        setPerformancePrice(data.performance_price ?? []);
        setAttendanceOverview(data.attendance_overview ?? []);
        setAdvancedAttendance(data.advanced_attendance ?? []);
        if (data.filter_options.divisions.length > 0)
          setSelectedDivision(data.filter_options.divisions[0]);
        if (data.filter_options.teams.length > 0)
          setSelectedTeam(data.filter_options.teams[0]);
        if (data.attendance_teams.length > 0)
          setSelectedAttTeam(data.attendance_teams[0]);
      })
      .catch(() => {
        // Fallback to individual calls
        Promise.all([
          getUpcomingGames(),
          getTeamPrices(),
          getPriceSpread(),
          getPriceTrendsByTeam(),
          getPriceTrends(),
          getPriceAttendanceCorrelation(),
          getAttendanceTeams(),
          getTicketFilterOptions(),
        ]).then(([u, tp, sp, tt, pt, corr, at, fo]) => {
          setAllUpcoming(u);
          setAllTeamPrices(tp);
          setAllSpread(sp);
          setAllTeamTrends(tt);
          setAllPriceTrends(pt);
          setCorrelation(corr);
          setAttTeams(at);
          setDivisions(fo.divisions);
          setTeams(fo.teams);
          if (fo.divisions.length > 0) setSelectedDivision(fo.divisions[0]);
          if (fo.teams.length > 0) setSelectedTeam(fo.teams[0]);
          if (at.length > 0) setSelectedAttTeam(at[0]);
        });
      })
      .finally(() => setLoading(false));
  }, []);

  // Attendance per team (separate small call)
  useEffect(() => {
    if (selectedAttTeam) {
      getAttendance({ team_abbrev: selectedAttTeam }).then(setAttendance);
    }
  }, [selectedAttTeam]);

  // ── Client-side filtering via useMemo ──

  const allowedTeams = useMemo(() => {
    if (filterMode === "team" && selectedTeam) return new Set([selectedTeam]);
    if (filterMode === "division" && selectedDivision) {
      return new Set(
        Object.entries(teamDivisions)
          .filter(([, div]) => div === selectedDivision)
          .map(([abbr]) => abbr)
      );
    }
    return null; // no filter
  }, [filterMode, selectedDivision, selectedTeam, teamDivisions]);

  const upcoming = useMemo(() => {
    if (!allowedTeams) return allUpcoming;
    return allUpcoming.filter((g) => allowedTeams.has(g.home_team));
  }, [allUpcoming, allowedTeams]);

  const summary: TicketSummary | null = useMemo(() => {
    if (allUpcoming.length === 0) return null;
    const games = upcoming;
    if (games.length === 0) {
      return {
        avg_price: null,
        lowest_price: null,
        highest_price: null,
        avg_spread: null,
        total_listings: null,
        games_tracked: 0,
        snapshot_date: null,
      };
    }
    const prices = games.filter((g) => g.avg_price != null).map((g) => g.avg_price!);
    const lows = games.filter((g) => g.low_price != null).map((g) => g.low_price!);
    const highs = games.filter((g) => g.high_price != null).map((g) => g.high_price!);
    const spreads = games.filter((g) => g.spread != null).map((g) => g.spread!);
    const listings = games.filter((g) => g.listings != null).map((g) => g.listings!);

    return {
      avg_price: prices.length > 0 ? Math.round(prices.reduce((a, b) => a + b, 0) / prices.length) : null,
      lowest_price: lows.length > 0 ? Math.min(...lows) : null,
      highest_price: highs.length > 0 ? Math.max(...highs) : null,
      avg_spread: spreads.length > 0 ? Math.round(spreads.reduce((a, b) => a + b, 0) / spreads.length) : null,
      total_listings: listings.length > 0 ? listings.reduce((a, b) => a + b, 0) : null,
      games_tracked: games.length,
      snapshot_date: null,
    };
  }, [upcoming, allUpcoming.length]);

  const teamPrices = useMemo(() => {
    if (!allowedTeams) return allTeamPrices;
    return allTeamPrices.filter((tp) => allowedTeams.has(tp.team));
  }, [allTeamPrices, allowedTeams]);

  const spreadData = useMemo(() => {
    if (!allowedTeams) return allSpread;
    return allSpread.filter((s) => allowedTeams.has(s.team));
  }, [allSpread, allowedTeams]);

  const teamTrends = useMemo(() => {
    if (!allowedTeams) return allTeamTrends;
    return allTeamTrends.filter((t) => allowedTeams.has(t.team));
  }, [allTeamTrends, allowedTeams]);

  const trends = useMemo(() => {
    if (!allowedTeams) return allPriceTrends;
    // Recompute from filtered upcoming data — group by approximated days_until_game
    // Since we don't have days_until_game in upcoming, use the unfiltered price trends as league average
    return allPriceTrends;
  }, [allPriceTrends, allowedTeams]);

  // ── Filter handlers (instant, no network) ──

  const handleFilterModeChange = (val: string) => {
    setFilterMode(val as FilterMode);
  };

  const handleDivisionChange = (val: string) => {
    setSelectedDivision(val);
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

          {/* Performance vs Ticket Price */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Performance vs Ticket Price</h2>
          {performancePrice.length > 0 ? (
            <PlotlyChart
              data={[
                {
                  x: performancePrice.map((p) => p.avg_ticket_price),
                  y: performancePrice.map((p) => p.win_pct),
                  text: performancePrice.map((p) => p.team),
                  type: "scatter",
                  mode: "markers+text",
                  textposition: "top center",
                  textfont: { color: "#c9d1d9", size: 10 },
                  marker: {
                    color: "#1f6feb",
                    size: performancePrice.map((p) => Math.max(p.goals_per_game * 10, 8)),
                    opacity: 0.8,
                  },
                  hovertemplate: performancePrice.map(
                    (p) =>
                      `<b>${p.team}</b><br>Win%: ${(p.win_pct * 100).toFixed(1)}%<br>Goals/Game: ${p.goals_per_game}<br>Shots/Game: ${p.shots_per_game}<br>Avg Price: $${Math.round(p.avg_ticket_price)}<extra></extra>`
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
                  title: "Win Percentage",
                  gridcolor: "#21262d",
                  zerolinecolor: "#21262d",
                  tickformat: ".0%",
                },
                showlegend: false,
              }}
            />
          ) : (
            <InfoBox text="No performance-price data available. Requires both game_team_stats (Kaggle import) and ticket snapshot data." />
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

      {/* League Attendance Trends */}
      <h2 className="text-lg font-bold text-text-bright mb-4">League Attendance Trends</h2>
      {attendanceOverview.length > 0 ? (
        <PlotlyChart
          data={(() => {
            const byDiv = new Map<string, AttendanceOverviewPoint[]>();
            for (const pt of attendanceOverview) {
              const arr = byDiv.get(pt.division) ?? [];
              arr.push(pt);
              byDiv.set(pt.division, arr);
            }
            return Array.from(byDiv.entries()).map(([div, points], i) => {
              const sorted = points.sort((a, b) => a.season_id - b.season_id);
              return {
                x: sorted.map((p) => p.season_display),
                y: sorted.map((p) => p.avg_attendance),
                type: "scatter" as const,
                mode: "lines+markers" as const,
                name: div,
                marker: { color: TEAM_COLORS[i % TEAM_COLORS.length], size: 6 },
                line: { color: TEAM_COLORS[i % TEAM_COLORS.length], width: 2 },
                hovertemplate: sorted.map(
                  (p) =>
                    `<b>${div}</b><br>${p.season_display}<br>Avg: ${Math.round(p.avg_attendance).toLocaleString()}<br>Games: ${p.games_count}<extra></extra>`
                ),
              };
            });
          })()}
          layout={{
            xaxis: { title: "Season", gridcolor: "#21262d", zerolinecolor: "#21262d" },
            yaxis: {
              title: "Average Attendance",
              gridcolor: "#21262d",
              zerolinecolor: "#21262d",
            },
            showlegend: true,
            legend: { font: { color: "#c9d1d9" } },
          }}
        />
      ) : (
        <InfoBox text="No attendance overview data available. Requires games with attendance data." />
      )}

      {/* Per-Team Attendance */}
      <h3 className="text-md font-bold text-text-bright mt-6 mb-4">Team Attendance History</h3>
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

      <hr className="border-border my-8" />

      {/* Advanced Metrics & Attendance */}
      <h2 className="text-lg font-bold text-text-bright mb-4">Expected Goals vs Attendance</h2>
      {advancedAttendance.length > 0 ? (
        <PlotlyChart
          data={[
            {
              x: advancedAttendance.map((a) => a.x_goals_pct),
              y: advancedAttendance.map((a) => a.avg_attendance),
              text: advancedAttendance.map((a) => a.team),
              type: "scatter",
              mode: "markers+text",
              textposition: "top center",
              textfont: { color: "#c9d1d9", size: 10 },
              marker: {
                color: advancedAttendance.map((a) => a.corsi_pct),
                colorscale: [
                  [0, "#da3633"],
                  [0.5, "#1f6feb"],
                  [1, "#58a6ff"],
                ],
                size: advancedAttendance.map((a) => Math.max((a.fenwick_pct - 46) * 4, 6)),
                opacity: 0.85,
                colorbar: {
                  title: { text: "Corsi%", font: { color: "#c9d1d9" } },
                  tickfont: { color: "#c9d1d9" },
                  ticksuffix: "%",
                },
              },
              hovertemplate: advancedAttendance.map(
                (a) =>
                  `<b>${a.team}</b><br>xGoals%: ${a.x_goals_pct.toFixed(1)}%<br>Corsi%: ${a.corsi_pct.toFixed(1)}%<br>Fenwick%: ${a.fenwick_pct.toFixed(1)}%<br>Avg Attendance: ${Math.round(a.avg_attendance).toLocaleString()}<extra></extra>`
              ),
            },
          ]}
          layout={{
            xaxis: {
              title: "Expected Goals % (Team Quality)",
              gridcolor: "#21262d",
              zerolinecolor: "#21262d",
              ticksuffix: "%",
            },
            yaxis: {
              title: "Average Attendance",
              gridcolor: "#21262d",
              zerolinecolor: "#21262d",
            },
            showlegend: false,
          }}
        />
      ) : (
        <InfoBox text="No advanced metrics data available. Requires game_advanced_stats (Kaggle import) and games with attendance data." />
      )}
    </>
  );
}
