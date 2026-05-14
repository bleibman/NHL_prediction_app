"use client";

import { useEffect, useState, useMemo, useRef } from "react";
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
  getAnalyticsInit,
  getAttendance,
  getDivisionTrends,
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
  SeasonSummaryRow,
  PhysicalityRow,
  SpecialTeamsRow,
  HomeAdvantageRow,
  OvertimeRow,
  ShotQualityRow,
  DivisionTrendRow,
} from "@/lib/types";

function formatSeason(s: number): string {
  const start = Math.floor(s / 10000);
  const end = String(start + 1).slice(-2);
  return `${start}\u2013${end}`;
}

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
  // ── Team Analytics state ──
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number>(0);
  const [seasonSummary, setSeasonSummary] = useState<SeasonSummaryRow | null>(null);
  const [physicality, setPhysicality] = useState<PhysicalityRow[]>([]);
  const [specialTeams, setSpecialTeams] = useState<SpecialTeamsRow[]>([]);
  const [homeAdvantage, setHomeAdvantage] = useState<HomeAdvantageRow[]>([]);
  const [overtime, setOvertime] = useState<OvertimeRow[]>([]);
  const [shotQuality, setShotQuality] = useState<ShotQualityRow[]>([]);
  const [divisionTrends, setDivisionTrends] = useState<DivisionTrendRow[]>([]);
  const [trendMetric, setTrendMetric] = useState("points");
  const [analyticsLoading, setAnalyticsLoading] = useState(true);

  // ── Ticket data state (existing) ──
  const [allUpcoming, setAllUpcoming] = useState<UpcomingGame[]>([]);
  const [allTeamPrices, setAllTeamPrices] = useState<TeamPrice[]>([]);
  const [allSpread, setAllSpread] = useState<PriceSpreadPoint[]>([]);
  const [allTeamTrends, setAllTeamTrends] = useState<TeamPriceTrendPoint[]>([]);
  const [allPriceTrends, setAllPriceTrends] = useState<PriceTrendPoint[]>([]);
  const [correlation, setCorrelation] = useState<PriceAttendancePoint[]>([]);
  const [attTeams, setAttTeams] = useState<string[]>([]);
  const [teamDivisions, setTeamDivisions] = useState<Record<string, string>>({});
  const [performancePrice, setPerformancePrice] = useState<PerformancePricePoint[]>([]);
  const [attendanceOverview, setAttendanceOverview] = useState<AttendanceOverviewPoint[]>([]);
  const [advancedAttendance, setAdvancedAttendance] = useState<AdvancedAttendancePoint[]>([]);

  // Attendance (separate call per team)
  const [selectedAttTeam, setSelectedAttTeam] = useState("");
  const [attendance, setAttendance] = useState<AttendancePoint[]>([]);

  const [ticketLoading, setTicketLoading] = useState(true);

  // Tab state
  const [activeTab, setActiveTab] = useState<"performance" | "tickets">("performance");

  // Filter state
  const [divisions, setDivisions] = useState<string[]>([]);
  const [teams, setTeams] = useState<string[]>([]);
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [selectedDivision, setSelectedDivision] = useState("");
  const [selectedTeam, setSelectedTeam] = useState("");

  // Track which season is already loaded to avoid double-fetch
  const loadedSeasonRef = useRef<number>(0);

  // ── Load team analytics ──
  useEffect(() => {
    getAnalyticsInit()
      .then((data) => {
        setSeasons(data.seasons);
        const initSeason = data.selected_season ?? (data.seasons.length > 0 ? data.seasons[0] : 0);
        if (initSeason) {
          setSelectedSeason(initSeason);
          loadedSeasonRef.current = initSeason;
        }
        setSeasonSummary(data.season_summary);
        setPhysicality(data.physicality);
        setSpecialTeams(data.special_teams);
        setHomeAdvantage(data.home_advantage);
        setOvertime(data.overtime);
        setShotQuality(data.shot_quality);
        setDivisionTrends(data.division_trends);
        setTeamDivisions(data.team_divisions);
        setDivisions(data.filter_options.divisions);
        setTeams(data.filter_options.teams);
        if (data.filter_options.divisions.length > 0)
          setSelectedDivision(data.filter_options.divisions[0]);
        if (data.filter_options.teams.length > 0)
          setSelectedTeam(data.filter_options.teams[0]);
      })
      .catch(() => {})
      .finally(() => setAnalyticsLoading(false));
  }, []);

  // Season change -> reload analytics (skip if already loaded by init)
  useEffect(() => {
    if (!selectedSeason || selectedSeason === loadedSeasonRef.current) return;
    loadedSeasonRef.current = selectedSeason;
    setAnalyticsLoading(true);
    getAnalyticsInit(selectedSeason)
      .then((data) => {
        setSeasonSummary(data.season_summary);
        setPhysicality(data.physicality);
        setSpecialTeams(data.special_teams);
        setHomeAdvantage(data.home_advantage);
        setOvertime(data.overtime);
        setShotQuality(data.shot_quality);
        setDivisionTrends(data.division_trends);
      })
      .catch(() => {})
      .finally(() => setAnalyticsLoading(false));
  }, [selectedSeason]);

  // ── Load ticket data lazily when Tickets tab is first selected ──
  const ticketLoadedRef = useRef(false);
  useEffect(() => {
    if (activeTab !== "tickets" || ticketLoadedRef.current) return;
    ticketLoadedRef.current = true;
    getTicketsInit()
      .then((data) => {
        setAllUpcoming(data.upcoming);
        setAllTeamPrices(data.team_prices);
        setAllSpread(data.spread);
        setAllTeamTrends(data.team_trends);
        setAllPriceTrends(data.price_trends);
        setCorrelation(data.correlation);
        setAttTeams(data.attendance_teams);
        setPerformancePrice(data.performance_price ?? []);
        setAttendanceOverview(data.attendance_overview ?? []);
        setAdvancedAttendance(data.advanced_attendance ?? []);
        if (data.attendance_teams.length > 0)
          setSelectedAttTeam(data.attendance_teams[0]);
      })
      .catch(() => {})
      .finally(() => setTicketLoading(false));
  }, [activeTab]);

  // Metric change -> reload division trends
  useEffect(() => {
    if (trendMetric === "points") return; // already loaded from init
    getDivisionTrends(trendMetric)
      .then(setDivisionTrends)
      .catch(() => {});
  }, [trendMetric]);

  // Attendance per team
  useEffect(() => {
    if (selectedAttTeam) {
      getAttendance({ team_abbrev: selectedAttTeam }).then(setAttendance);
    }
  }, [selectedAttTeam]);

  // ── Client-side filtering ──

  const allowedTeams = useMemo(() => {
    if (filterMode === "team" && selectedTeam) return new Set([selectedTeam]);
    if (filterMode === "division" && selectedDivision) {
      return new Set(
        Object.entries(teamDivisions)
          .filter(([, div]) => div === selectedDivision)
          .map(([abbr]) => abbr)
      );
    }
    return null;
  }, [filterMode, selectedDivision, selectedTeam, teamDivisions]);

  // Filter analytics data by team/division
  const filteredPhysicality = useMemo(() => {
    if (!allowedTeams) return physicality;
    return physicality.filter((p) => allowedTeams.has(p.team));
  }, [physicality, allowedTeams]);

  const filteredSpecialTeams = useMemo(() => {
    if (!allowedTeams) return specialTeams;
    return specialTeams.filter((s) => allowedTeams.has(s.team));
  }, [specialTeams, allowedTeams]);

  const filteredHomeAdvantage = useMemo(() => {
    if (!allowedTeams) return homeAdvantage;
    return homeAdvantage.filter((h) => allowedTeams.has(h.team));
  }, [homeAdvantage, allowedTeams]);

  const filteredOvertime = useMemo(() => {
    if (!allowedTeams) return overtime;
    return overtime.filter((o) => allowedTeams.has(o.team));
  }, [overtime, allowedTeams]);

  const filteredShotQuality = useMemo(() => {
    if (!allowedTeams) return shotQuality;
    return shotQuality.filter((s) => allowedTeams.has(s.team));
  }, [shotQuality, allowedTeams]);

  // Filter ticket data
  const upcoming = useMemo(() => {
    if (!allowedTeams) return allUpcoming;
    return allUpcoming.filter((g) => allowedTeams.has(g.home_team));
  }, [allUpcoming, allowedTeams]);

  const summary: TicketSummary | null = useMemo(() => {
    if (allUpcoming.length === 0) return null;
    const games = upcoming;
    if (games.length === 0) {
      return {
        avg_price: null, lowest_price: null, highest_price: null,
        avg_spread: null, total_listings: null, games_tracked: 0,
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
    return allPriceTrends;
  }, [allPriceTrends, allowedTeams]);

  const hasTicketData = summary && summary.games_tracked > 0;

  const showTeamLines = filterMode !== "all" && teamTrends.length > 0;

  const { trendChartData, trendSeries } = useMemo(() => {
    if (showTeamLines) {
      const byTeam = new Map<string, TeamPriceTrendPoint[]>();
      for (const pt of teamTrends) {
        const arr = byTeam.get(pt.team) ?? [];
        arr.push(pt);
        byTeam.set(pt.team, arr);
      }
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
        key: team, name: team, color: TEAM_COLORS[i % TEAM_COLORS.length],
      }));
      if (trends.length >= 2) {
        series.push({ key: "League Avg", name: "League Avg", color: "#484f58", dashed: true });
      }
      return { trendChartData: rows, trendSeries: series };
    }

    const rows = trends.map((t) => ({
      days_until_game: t.days_until_game, average_price: t.average_price,
    }));
    const series: SeriesConfig[] = [{ key: "average_price", name: "Average Price", color: "#1f6feb" }];
    return { trendChartData: rows, trendSeries: series };
  }, [showTeamLines, teamTrends, trends]);

  // Division trends chart data
  const divisionTrendChartData = useMemo(() => {
    if (divisionTrends.length === 0) return { data: [], lines: [] as { key: string; name: string; color: string }[] };

    const byDiv = new Map<string, DivisionTrendRow[]>();
    for (const pt of divisionTrends) {
      const arr = byDiv.get(pt.division) ?? [];
      arr.push(pt);
      byDiv.set(pt.division, arr);
    }
    const divNames = Array.from(byDiv.keys());
    const allSeasons = new Set<string>();
    for (const pts of byDiv.values()) {
      for (const p of pts) allSeasons.add(p.season_display);
    }
    const data = Array.from(allSeasons)
      .sort()
      .map((season) => {
        const row: Record<string, unknown> = { season };
        for (const [div, pts] of byDiv.entries()) {
          const match = pts.find((p) => p.season_display === season);
          if (match) row[div] = match.metric_value;
        }
        return row;
      });
    const lines = divNames.map((div, i) => ({
      key: div, name: div, color: TEAM_COLORS[i % TEAM_COLORS.length],
    }));
    return { data, lines };
  }, [divisionTrends]);

  const filterModeOptions = [
    { value: "all", label: "All Teams" },
    { value: "division", label: "By Division" },
    { value: "team", label: "Individual Team" },
  ];
  const divisionOptions = divisions.map((d) => ({ value: d, label: d }));
  const teamOptions = teams.map((t) => ({ value: t, label: t }));
  const seasonOptions = seasons.map((s) => ({ value: String(s), label: formatSeason(s) }));
  const trendMetricOptions = [
    { value: "points", label: "Points" },
    { value: "gf_pg", label: "Goals For/G" },
    { value: "ga_pg", label: "Goals Against/G" },
    { value: "pp_pct", label: "PP%" },
    { value: "pk_pct", label: "PK%" },
  ];

  if (analyticsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <>
      <PageHeader title="Team Analytics" subtitle="NHL team performance metrics, trends, and ticket data" />

      {/* Tab bar */}
      <div className="flex border-b border-border mb-6">
        <button
          onClick={() => setActiveTab("performance")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "performance"
              ? "border-primary text-primary-light"
              : "border-transparent text-text-muted hover:text-text hover:border-border"
          }`}
        >
          Team Performance
        </button>
        <button
          onClick={() => setActiveTab("tickets")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
            activeTab === "tickets"
              ? "border-primary text-primary-light"
              : "border-transparent text-text-muted hover:text-text hover:border-border"
          }`}
        >
          Tickets &amp; Attendance
        </button>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        {activeTab === "performance" && seasonOptions.length > 0 && (
          <Select
            options={seasonOptions}
            value={String(selectedSeason)}
            onChange={(v) => setSelectedSeason(Number(v))}
          />
        )}
        <Select
          options={filterModeOptions}
          value={filterMode}
          onChange={(v) => setFilterMode(v as FilterMode)}
        />
        {filterMode === "division" && divisionOptions.length > 0 && (
          <Select
            options={divisionOptions}
            value={selectedDivision}
            onChange={setSelectedDivision}
          />
        )}
        {filterMode === "team" && teamOptions.length > 0 && (
          <Select
            options={teamOptions}
            value={selectedTeam}
            onChange={setSelectedTeam}
          />
        )}
      </div>

      {/* ═══════════════════════════════════════════════════════ */}
      {/* TAB 1: TEAM PERFORMANCE */}
      {/* ═══════════════════════════════════════════════════════ */}

      {activeTab === "performance" && (
        <>
          {/* 1. Season Summary Cards */}
          {seasonSummary ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
              <StatCard label="Teams" value={String(seasonSummary.teams_count)} />
              <StatCard label="Total Games" value={seasonSummary.total_games.toLocaleString()} />
              <StatCard label="Avg Goals/Game" value={seasonSummary.avg_goals_per_game.toFixed(2)} />
              <StatCard label="Avg Hits/Game" value={seasonSummary.avg_hits_per_game.toFixed(1)} />
              <StatCard label="OT/SO Games" value={String(seasonSummary.ot_games)} />
            </div>
          ) : (
            <InfoBox text="No game stats data available for this season." />
          )}

          {/* 2. Physical Play Rankings */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Physical Play Rankings</h2>
          {filteredPhysicality.length > 0 ? (
            <HorizontalBarChart
              data={filteredPhysicality}
              xKey="hits_pg"
              yKey="team"
              colorScale={["#21262d", "#da3633", "#ff7b72"]}
              labelFormatter={(v) => `${Number(v).toFixed(1)}`}
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>Hits/G: {Number(p.hits_pg).toFixed(1)}</div>
                  <div>PIM/G: {Number(p.pim_pg).toFixed(1)}</div>
                  <div>Blocked/G: {Number(p.blocked_pg).toFixed(1)}</div>
                  <div>Takeaways/G: {Number(p.takeaways_pg).toFixed(1)}</div>
                  <div>Giveaways/G: {Number(p.giveaways_pg).toFixed(1)}</div>
                </>
              )}
              xAxisLabel="Hits Per Game"
              height={Math.max(400, filteredPhysicality.length * 28)}
            />
          ) : (
            <InfoBox text="No physicality data available for this season/filter." />
          )}

          <hr className="border-border my-8" />

          {/* 3. Special Teams Efficiency */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Special Teams Efficiency</h2>
          {filteredSpecialTeams.length > 0 ? (
            <BubbleScatterChart
              data={filteredSpecialTeams.map((s) => ({
                ...s,
                bubble_size: Math.max(s.pp_opportunities_pg * 15, 8),
              }))}
              xKey="pp_pct"
              yKey="pk_pct"
              sizeKey="bubble_size"
              labelKey="team"
              xAxisLabel="Power Play % (PP%)"
              yAxisLabel="Penalty Kill % (PK%)"
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>PP%: {Number(p.pp_pct).toFixed(1)}%</div>
                  <div>PK%: {Number(p.pk_pct).toFixed(1)}%</div>
                  <div>PP Opps/G: {Number(p.pp_opportunities_pg).toFixed(2)}</div>
                </>
              )}
            />
          ) : (
            <InfoBox text="No special teams data available for this season/filter." />
          )}

          <hr className="border-border my-8" />

          {/* 4. Home Ice Advantage */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Home Ice Advantage</h2>
          {filteredHomeAdvantage.length > 0 ? (
            <HorizontalBarChart
              data={filteredHomeAdvantage}
              xKey="differential"
              yKey="team"
              colorScale={["#da3633", "#d29922", "#238636"]}
              labelFormatter={(v) => `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(1)}%`}
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>Home Win%: {Number(p.home_win_pct).toFixed(1)}%</div>
                  <div>Away Win%: {Number(p.away_win_pct).toFixed(1)}%</div>
                  <div>Differential: {Number(p.differential) > 0 ? "+" : ""}{Number(p.differential).toFixed(1)}%</div>
                </>
              )}
              xAxisLabel="Home vs Away Win% Differential"
              height={Math.max(400, filteredHomeAdvantage.length * 28)}
            />
          ) : (
            <InfoBox text="No home advantage data available for this season/filter." />
          )}

          <hr className="border-border my-8" />

          {/* 5. Overtime & Shootout Breakdown */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Overtime &amp; Shootout Performance</h2>
          {filteredOvertime.length > 0 ? (
            <HorizontalBarChart
              data={filteredOvertime}
              xKey="ot_so_win_rate"
              yKey="team"
              colorScale={["#da3633", "#d29922", "#238636"]}
              labelFormatter={(v) => `${Number(v).toFixed(1)}%`}
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>OT+SO Win Rate: {Number(p.ot_so_win_rate).toFixed(1)}%</div>
                  <div>REG: {String(p.reg_wins)}W / {String(p.reg_losses)}L</div>
                  <div>OT: {String(p.ot_wins)}W / {String(p.ot_losses)}L</div>
                  <div>SO: {String(p.so_wins)}W / {String(p.so_losses)}L</div>
                </>
              )}
              xAxisLabel="OT + Shootout Win Rate (%)"
              height={Math.max(400, filteredOvertime.length * 28)}
            />
          ) : (
            <InfoBox text="No overtime data available for this season/filter." />
          )}

          <hr className="border-border my-8" />

          {/* 6. Shot Quality Profile */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Shot Quality Profile (Advanced)</h2>
          {filteredShotQuality.length > 0 ? (
            <BubbleScatterChart
              data={filteredShotQuality.map((s) => ({
                ...s,
                bubble_size: Math.max((s.x_goals_pct - 44) * 4, 6),
              }))}
              xKey="corsi_pct"
              yKey="x_goals_pct"
              sizeKey="bubble_size"
              labelKey="team"
              xAxisLabel="Corsi% (Shot Attempt Share)"
              yAxisLabel="Expected Goals% (xG%)"
              tooltipFormatter={(p) => (
                <>
                  <div style={{ fontWeight: 600 }}>{String(p.team)}</div>
                  <div>Corsi%: {Number(p.corsi_pct).toFixed(1)}%</div>
                  <div>xGoals%: {Number(p.x_goals_pct).toFixed(1)}%</div>
                </>
              )}
            />
          ) : (
            <InfoBox text="No advanced shot quality data available for this season. Advanced stats are available for 2008\u20132022 seasons." />
          )}

          <hr className="border-border my-8" />

          {/* 7. Division Performance Trends */}
          <h2 className="text-lg font-bold text-text-bright mb-4">Division Performance Trends</h2>
          <div className="mb-4">
            <Select
              options={trendMetricOptions}
              value={trendMetric}
              onChange={setTrendMetric}
            />
          </div>
          {divisionTrendChartData.data.length > 0 ? (
            <MultiLineChart
              data={divisionTrendChartData.data}
              xKey="season"
              lines={divisionTrendChartData.lines}
              xAxisLabel="Season"
              yAxisLabel={trendMetricOptions.find((o) => o.value === trendMetric)?.label ?? "Value"}
            />
          ) : (
            <InfoBox text="No division trend data available. Requires season_stats data." />
          )}
        </>
      )}

      {/* ═══════════════════════════════════════════════════════ */}
      {/* TAB 2: TICKETS & ATTENDANCE */}
      {/* ═══════════════════════════════════════════════════════ */}

      {activeTab === "tickets" && (ticketLoading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
        </div>
      ) : (
        <>
          {!hasTicketData ? (
            <InfoBox text="No ticket data available yet. Set SEATGEEK_CLIENT_ID in your environment and run Data Refresh to fetch ticket prices." />
          ) : (
            <>
              {/* Ticket Summary cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
                <StatCard
                  label="Avg Ticket Price"
                  value={summary!.avg_price != null ? `$${Math.round(summary!.avg_price)}` : "N/A"}
                />
                <StatCard
                  label="Lowest Available"
                  value={summary!.lowest_price != null ? `$${summary!.lowest_price}` : "N/A"}
                />
                <StatCard
                  label="Avg Spread"
                  value={summary!.avg_spread != null ? `$${Math.round(summary!.avg_spread)}` : "N/A"}
                />
                <StatCard
                  label="Total Listings"
                  value={summary!.total_listings != null ? summary!.total_listings.toLocaleString() : "N/A"}
                />
                <StatCard
                  label="Games Tracked"
                  value={summary!.games_tracked.toString()}
                  sub={summary!.snapshot_date ? `as of ${summary!.snapshot_date}` : undefined}
                />
              </div>

              {/* Upcoming Games */}
              <h3 className="text-lg font-bold text-text-bright mb-4">Upcoming Games</h3>
              <DataTable columns={gameColumns} data={upcoming} />

              <hr className="border-border my-8" />

              {/* Price Trends */}
              <h3 className="text-lg font-bold text-text-bright mb-4">
                Price Trends {filterMode !== "all" ? "(by Team)" : ""}
              </h3>
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
                <InfoBox text="Price trend analysis requires at least 2 days of snapshot data." />
              )}

              <hr className="border-border my-8" />

              {/* Price Spread */}
              <h3 className="text-lg font-bold text-text-bright mb-4">Price Spread by Team</h3>
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
              <h3 className="text-lg font-bold text-text-bright mb-4">Average Price by Team</h3>
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
              <h3 className="text-lg font-bold text-text-bright mb-4">Performance vs Ticket Price</h3>
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
                <InfoBox text="No performance-price data available. Requires both game_team_stats and ticket snapshot data." />
              )}

              <hr className="border-border my-8" />

              {/* Price vs Attendance Correlation */}
              <h3 className="text-lg font-bold text-text-bright mb-4">
                Price vs Attendance (Capacity Utilization)
              </h3>
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
          <h3 className="text-lg font-bold text-text-bright mb-4">League Attendance Trends</h3>
          {attendanceOverview.length > 0 ? (
            (() => {
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
                key: div, name: div, color: TEAM_COLORS[i % TEAM_COLORS.length],
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
          <h3 className="text-lg font-bold text-text-bright mb-4">Expected Goals vs Attendance</h3>
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
            <InfoBox text="No advanced metrics data available. Requires game_advanced_stats and games with attendance data." />
          )}
        </>
      ))}
    </>
  );
}
