"use client";

import { useEffect, useState } from "react";
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
  getTeamPrices,
  getAttendance,
  getAttendanceTeams,
} from "@/lib/api";
import type {
  TicketSummary,
  UpcomingGame,
  PriceTrendPoint,
  TeamPrice,
  AttendancePoint,
} from "@/lib/types";

const gameCol = createColumnHelper<UpcomingGame>();
const gameColumns = [
  gameCol.accessor("date", { header: "Date" }),
  gameCol.accessor("home_team", { header: "Home" }),
  gameCol.accessor("away_team", { header: "Away" }),
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
  gameCol.accessor("listings", {
    header: "Listings",
    cell: (info) => info.getValue()?.toLocaleString() ?? "\u2014",
  }),
];

export default function TicketsPage() {
  const [summary, setSummary] = useState<TicketSummary | null>(null);
  const [upcoming, setUpcoming] = useState<UpcomingGame[]>([]);
  const [trends, setTrends] = useState<PriceTrendPoint[]>([]);
  const [teamPrices, setTeamPrices] = useState<TeamPrice[]>([]);
  const [attTeams, setAttTeams] = useState<string[]>([]);
  const [selectedAttTeam, setSelectedAttTeam] = useState("");
  const [attendance, setAttendance] = useState<AttendancePoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getTicketSummary(),
      getUpcomingGames(),
      getPriceTrends(),
      getTeamPrices(),
      getAttendanceTeams(),
    ])
      .then(([s, u, t, tp, at]) => {
        setSummary(s);
        setUpcoming(u);
        setTrends(t);
        setTeamPrices(tp);
        setAttTeams(at);
        if (at.length > 0) setSelectedAttTeam(at[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selectedAttTeam) {
      getAttendance(selectedAttTeam).then(setAttendance);
    }
  }, [selectedAttTeam]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  const hasTicketData = summary && summary.games_tracked > 0;

  return (
    <>
      <PageHeader title="Ticket Analytics" subtitle="NHL ticket prices, trends, and attendance data" />

      {!hasTicketData ? (
        <InfoBox text="No ticket data available yet. Set SEATGEEK_CLIENT_ID in your environment and run Data Refresh to fetch ticket prices." />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              label="Avg Ticket Price"
              value={summary.avg_price != null ? `$${Math.round(summary.avg_price)}` : "N/A"}
            />
            <StatCard
              label="Lowest Available"
              value={summary.lowest_price != null ? `$${summary.lowest_price}` : "N/A"}
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

          <h2 className="text-lg font-bold text-text-bright mb-4">Upcoming Games</h2>
          <DataTable columns={gameColumns} data={upcoming} />

          <hr className="border-border my-8" />

          <h2 className="text-lg font-bold text-text-bright mb-4">Price Trends</h2>
          {trends.length >= 2 ? (
            <PlotlyChart
              data={[
                {
                  x: trends.map((t) => t.days_until_game),
                  y: trends.map((t) => t.average_price),
                  type: "scatter",
                  mode: "lines+markers",
                  marker: { color: "#1f6feb", size: 6 },
                  line: { color: "#1f6feb", width: 2.5 },
                },
              ]}
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
                showlegend: false,
              }}
            />
          ) : (
            <InfoBox text="Price trend analysis requires at least 2 days of snapshot data. Run the daily ticket fetch to accumulate history." />
          )}

          <hr className="border-border my-8" />

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
        </>
      )}

      <hr className="border-border my-8" />

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
