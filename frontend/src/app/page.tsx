"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import StatCard from "@/components/cards/StatCard";
import { getDashboardSummary, getDashboardTopScorers } from "@/lib/api";
import { formatSeason } from "@/lib/utils";
import type { DashboardSummary, ScorerRow } from "@/lib/types";

const FEATURE_CARDS = [
  {
    href: "/dashboard",
    title: "Dashboard",
    description: "Live standings, division rankings, and top scorers for the current season.",
    iconBg: "bg-primary-light/10",
    iconColor: "text-primary-light",
    hoverBorder: "hover:border-primary-light/50",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    href: "/historical",
    title: "Historical Data",
    description: "Browse 20 seasons of stats, playoff results, and team performance trends.",
    iconBg: "bg-accent-green/10",
    iconColor: "text-accent-green",
    hoverBorder: "hover:border-accent-green/50",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
  },
  {
    href: "/predictions",
    title: "Predictions",
    description: "ML-powered bracket simulation with 5,000 Monte Carlo iterations.",
    iconBg: "bg-accent-orange/10",
    iconColor: "text-accent-orange",
    hoverBorder: "hover:border-accent-orange/50",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
  {
    href: "/tickets",
    title: "Ticket Analytics",
    description: "SeatGeek price tracking, trends, team comparisons, and attendance data.",
    iconBg: "bg-accent-red/10",
    iconColor: "text-accent-red",
    hoverBorder: "hover:border-accent-red/50",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
      </svg>
    ),
  },
];

export default function Home() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [scorers, setScorers] = useState<ScorerRow[] | null>(null);
  const [summaryError, setSummaryError] = useState(false);
  const [scorersError, setScorersError] = useState(false);

  useEffect(() => {
    Promise.all([
      getDashboardSummary()
        .then(setSummary)
        .catch(() => setSummaryError(true)),
      getDashboardTopScorers(5)
        .then(setScorers)
        .catch(() => setScorersError(true)),
    ]);
  }, []);

  return (
    <div className="-m-8">
      {/* ─── Hero ─── */}
      <section className="bg-gradient-to-br from-bg-card to-bg border-b border-border p-10">
        <div className="max-w-2xl">
          <h1 className="text-4xl font-bold text-text-bright mb-3">
            NHL Stanley Cup Prediction Engine
          </h1>
          <p className="text-text-muted text-lg leading-relaxed mb-6">
            Machine learning predictions, live standings, historical analysis, and ticket
            price analytics — all in one place.
          </p>
          <div className="flex gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors"
            >
              Explore Dashboard
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <Link
              href="/predictions"
              className="inline-flex items-center gap-2 px-5 py-2.5 border border-border hover:border-primary/50 text-text hover:text-text-bright rounded-lg font-medium transition-colors"
            >
              Run Predictions
            </Link>
          </div>
        </div>
      </section>

      {/* ─── Live Season Summary ─── */}
      <section className="p-8">
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
          Live Season Summary
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {summary ? (
            <>
              <StatCard label="Season" value={formatSeason(summary.season_id)} />
              <StatCard label="Games Played" value={summary.games_count.toLocaleString()} />
              <StatCard label="Playoff Series" value={String(summary.playoff_series_count)} />
              <StatCard label="Players Tracked" value={summary.players_count.toLocaleString()} />
            </>
          ) : summaryError ? (
            <>
              <StatCard label="Season" value="---" />
              <StatCard label="Games Played" value="---" />
              <StatCard label="Playoff Series" value="---" />
              <StatCard label="Players Tracked" value="---" />
            </>
          ) : (
            Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="bg-bg-card border border-border rounded-xl p-5">
                <div className="h-3 w-20 bg-border rounded animate-pulse mb-3" />
                <div className="h-8 w-16 bg-border rounded animate-pulse" />
              </div>
            ))
          )}
        </div>
      </section>

      {/* ─── Features + Top Scorers ─── */}
      <section className="px-8 pb-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Feature Cards — 2x2 grid */}
          <div className="lg:col-span-2">
            <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
              Explore
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {FEATURE_CARDS.map((card) => (
                <Link
                  key={card.href}
                  href={card.href}
                  className={`group block bg-bg-card border border-border rounded-xl p-5 transition-all hover:-translate-y-1 ${card.hoverBorder}`}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={`p-2 rounded-lg ${card.iconBg} ${card.iconColor}`}>{card.icon}</div>
                    <svg
                      className="w-5 h-5 text-text-muted group-hover:text-text-bright transition-colors"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </div>
                  <h3 className="text-base font-semibold text-text-bright mb-1">{card.title}</h3>
                  <p className="text-sm text-text-muted leading-relaxed">{card.description}</p>
                </Link>
              ))}
            </div>
          </div>

          {/* Top Scorers */}
          <div>
            <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
              Top Scorers
            </h2>
            <div className="bg-bg-card border border-border rounded-xl overflow-hidden">
              {scorersError ? (
                <div className="px-5 py-8 text-center text-sm text-text-muted">
                  Unable to load scorers
                </div>
              ) : scorers ? (
                scorers.map((s, i) => (
                  <div
                    key={s.player_name}
                    className={`flex items-center gap-4 px-5 py-3 ${
                      i < scorers.length - 1 ? "border-b border-border" : ""
                    }`}
                  >
                    <span className="text-sm font-bold text-text-muted w-6 text-right">
                      {i + 1}
                    </span>
                    <span className="text-sm font-medium text-text-bright flex-1">
                      {s.player_name}
                    </span>
                    <span className="text-xs text-text-muted uppercase tracking-wide w-12 text-center">
                      {s.team}
                    </span>
                    <span className="text-sm font-semibold text-primary-light w-12 text-right">
                      {s.points} pts
                    </span>
                  </div>
                ))
              ) : (
                Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className={`flex items-center gap-4 px-5 py-3 ${
                      i < 4 ? "border-b border-border" : ""
                    }`}
                  >
                    <div className="h-4 w-4 bg-border rounded animate-pulse" />
                    <div className="h-4 w-32 bg-border rounded animate-pulse flex-1" />
                    <div className="h-4 w-10 bg-border rounded animate-pulse" />
                    <div className="h-4 w-12 bg-border rounded animate-pulse" />
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
