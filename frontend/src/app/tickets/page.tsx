"use client";

import { useEffect, useState, useMemo } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import PageHeader from "@/components/layout/PageHeader";
import StatCard from "@/components/cards/StatCard";
import InfoBox from "@/components/cards/InfoBox";
import DataTable from "@/components/ui/DataTable";
import Select from "@/components/ui/Select";
import HorizontalBarChart from "@/components/charts/HorizontalBarChart";
import TrendLineChart from "@/components/charts/TrendLineChart";
import type { SeriesConfig } from "@/components/charts/TrendLineChart";
import MultiLineChart from "@/components/charts/MultiLineChart";
import SimpleBarChart from "@/components/charts/SimpleBarChart";
import BubbleScatterChart from "@/components/charts/BubbleScatterChart";
import AdvancedScatterChart from "@/components/charts/AdvancedScatterChart";
import { TEAM_COLORS } from "@/components/charts/chartTheme";
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

  // Build price trends data for TrendLineChart
  const showTeamLines = filterMode !== "all" && teamTrends.length > 0;

  const { trendChartData, trendSeries } = useMemo(() => {
    if (showTeamLines) {
      const byTeam = new Map<string, TeamPriceTrendPoint[]>();
      for (const pt of teamTrends) {
        const arr = byTeam.get(pt.team) ?? [];
        arr.push(pt);
        byTeam.set(pt.team, arr);
      }
      // Collect all unique days_until_game values
      const allDays = new Set<number>();
      for (const pts of byTeam.values()) {
        for (const p of pts) allDays.add(p.days_until_game);
      }
      for (const t of trends) allDays.add(t.days_until_game);

      const teamNames = Array.from(byTeam.keys());
      const rows = Array.from(allDays)
        .sort((a, b) => a - b)
        .map((day) => {
          const row: Record<string, unknown> = { days_until_game: day };
          for (const [team, pts] of byTeam.entries()) {
            const match = pts.find((p) => p.days_until_game === day);
            if (match) row[team] = match.average_price;
          }
          const leagueMatch = trends.find((t) => t.days_until_game === day);
          if (leagueMatch) row["League Avg"] = leagueMatch.average_price;
          return row;
        });

      const series: SeriesConfig[] = teamNames.map((team, i) => ({
        key: team,
        name: team,
        color: TEAM_COLORS[i % TEAM_COLORS.length],
      }));
      if (trends.length >= 2) {
        series.push({ key: "League Avg", name: "League Avg", color: "#484f58", dashed: true });
      }
      return { trendChartData: rows, trendSeries: series };
    }

    // Simple league-wide trend
    const rows = trends.map((t) => ({
      days_until_game: t.days_until_game,
      average_price: t.average_price,
    }));
    const series: SeriesConfig[] = [{ key: "average_price", name: "Average Price", color: "#1f6feb" }];
    return { trendChartData: rows, trendSeries: series };
  }, [showTeamLines, teamTrends, trends]);

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
            <TrendLineChart
              data={trendChartData}
              xKey="days_until_game"
              series={trendSeries}
              reversedX
              showLegend={showTeamLines}
              xAxisLabel="Days Until Game"
              yAxisLabel="Average Price ($)"
            />
          ) : (
            <InfoBox text="Price trend analysis requires at least 2 days of snapshot data. Run the daily ticket fetch to accumulate history." />
          )}

          <hr className="border-border my-8" />

          {/* Price Spread */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Price Spread by Team</h2>
          {spreadData.length > 0 ? (
            <HorizontalBarChart
              data={spreadData}
              xKey="avg_spread"
              yKey="team"
              colorScale={["#238636", "#d29922", "#da3633"]}
              labelFormatter={(v) => `$${Math.round(Number(v))}`}
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>Spread: ${Math.round(Number(p.avg_spread))}</div>
                  <div>Avg Low: ${Math.round(Number(p.avg_lowest))}</div>
                  <div>Avg High: ${Math.round(Number(p.avg_highest))}</div>
                  <div>Listings: {String(p.listing_count)}</div>
                </>
              )}
              xAxisLabel="Average Price Spread ($)"
              height={Math.max(400, spreadData.length * 28)}
            />
          ) : (
            <InfoBox text="No spread data available for current filter." />
          )}

          <hr className="border-border my-8" />

          {/* Team Price Comparison */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Average Price by Team</h2>
          {teamPrices.length > 0 && (
            <HorizontalBarChart
              data={teamPrices}
              xKey="average_price"
              yKey="team"
              colorScale={["#21262d", "#1f6feb", "#58a6ff"]}
              labelFormatter={(v) => `$${Math.round(Number(v))}`}
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>Avg: ${Math.round(Number(p.average_price))}</div>
                  <div>Low: {p.lowest_price != null ? `$${Math.round(Number(p.lowest_price))}` : "N/A"}</div>
                  <div>High: {p.highest_price != null ? `$${Math.round(Number(p.highest_price))}` : "N/A"}</div>
                </>
              )}
              xAxisLabel="Average Ticket Price ($)"
              height={Math.max(400, teamPrices.length * 28)}
            />
          )}

          <hr className="border-border my-8" />

          {/* Performance vs Ticket Price */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Performance vs Ticket Price</h2>
          {performancePrice.length > 0 ? (
            <BubbleScatterChart
              data={performancePrice.map((p) => ({
                ...p,
                bubble_size: Math.max(p.goals_per_game * 10, 8),
              }))}
              xKey="avg_ticket_price"
              yKey="win_pct"
              sizeKey="bubble_size"
              labelKey="team"
              xAxisLabel="Average Ticket Price ($)"
              yAxisLabel="Win Percentage"
              yTickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>Win%: {(Number(p.win_pct) * 100).toFixed(1)}%</div>
                  <div>Goals/Game: {String(p.goals_per_game)}</div>
                  <div>Shots/Game: {String(p.shots_per_game)}</div>
                  <div>Avg Price: ${Math.round(Number(p.avg_ticket_price))}</div>
                </>
              )}
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
            <BubbleScatterChart
              data={correlation.map((c) => ({
                ...c,
                y_value: c.utilization_pct ?? c.avg_attendance,
              }))}
              xKey="avg_ticket_price"
              yKey="y_value"
              labelKey="team"
              fixedSize={144}
              xAxisLabel="Average Ticket Price ($)"
              yAxisLabel={
                correlation.some((c) => c.utilization_pct != null)
                  ? "Capacity Utilization (%)"
                  : "Average Attendance"
              }
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>Avg Price: ${Math.round(Number(p.avg_ticket_price))}</div>
                  <div>Avg Attendance: {Math.round(Number(p.avg_attendance)).toLocaleString()}</div>
                  <div>Capacity: {p.capacity != null ? Number(p.capacity).toLocaleString() : "N/A"}</div>
                  <div>Utilization: {p.utilization_pct != null ? `${p.utilization_pct}%` : "N/A"}</div>
                </>
              )}
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
        (() => {
          // Merge division data into a single array keyed by season
          const byDiv = new Map<string, AttendanceOverviewPoint[]>();
          for (const pt of attendanceOverview) {
            const arr = byDiv.get(pt.division) ?? [];
            arr.push(pt);
            byDiv.set(pt.division, arr);
          }
          const divNames = Array.from(byDiv.keys());
          const allSeasons = new Set<string>();
          for (const pts of byDiv.values()) {
            for (const p of pts) allSeasons.add(p.season_display);
          }
          const mergedData = Array.from(allSeasons)
            .sort()
            .map((season) => {
              const row: Record<string, unknown> = { season };
              for (const [div, pts] of byDiv.entries()) {
                const match = pts.find((p) => p.season_display === season);
                if (match) row[div] = match.avg_attendance;
              }
              return row;
            });
          const lines = divNames.map((div, i) => ({
            key: div,
            name: div,
            color: TEAM_COLORS[i % TEAM_COLORS.length],
          }));
          return (
            <MultiLineChart
              data={mergedData}
              xKey="season"
              lines={lines}
              xAxisLabel="Season"
              yAxisLabel="Average Attendance"
            />
          );
        })()
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
            <SimpleBarChart
              data={attendance}
              xKey="season_display"
              yKey="avg_attendance"
              yAxisLabel="Average Attendance"
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.season_display)}</div>
                  <div>Avg Attendance: {Math.round(Number(p.avg_attendance)).toLocaleString()}</div>
                </>
              )}
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
        <AdvancedScatterChart
          data={advancedAttendance.map((a) => ({
            ...a,
            fenwick_size: Math.max((a.fenwick_pct - 46) * 4, 6),
          }))}
          xKey="x_goals_pct"
          yKey="avg_attendance"
          colorKey="corsi_pct"
          sizeKey="fenwick_size"
          labelKey="team"
          colorScale={["#da3633", "#1f6feb", "#58a6ff"]}
          colorLabel="Corsi%"
          xTickSuffix="%"
          xAxisLabel="Expected Goals % (Team Quality)"
          yAxisLabel="Average Attendance"
          tooltipFormatter={(p) => (
            <>
              <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
              <div>xGoals%: {Number(p.x_goals_pct).toFixed(1)}%</div>
              <div>Corsi%: {Number(p.corsi_pct).toFixed(1)}%</div>
              <div>Fenwick%: {Number(p.fenwick_pct).toFixed(1)}%</div>
              <div>Avg Attendance: {Math.round(Number(p.avg_attendance)).toLocaleString()}</div>
            </>
          )}
        />
      ) : (
        <InfoBox text="No advanced metrics data available. Requires game_advanced_stats (Kaggle import) and games with attendance data." />
      )}
    </>
  );
}
