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
    accent: "primary-light",
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
    accent: "accent-green",
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
    accent: "accent-orange",
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
    accent: "accent-red",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
      </svg>
    ),
  },
];

const PIPELINE_STEPS = [
  {
    num: 1,
    title: "Collect",
    description: "Ingest game results, rosters, and ticket prices from NHL & SeatGeek APIs.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
    ),
  },
  {
    num: 2,
    title: "Train",
    description: "Fit a GradientBoosting classifier on historical playoff series outcomes.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    num: 3,
    title: "Predict",
    description: "Simulate 5,000 playoff brackets and rank teams by Cup probability.",
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
];

const ACCENT_CLASSES: Record<string, { border: string; text: string; bg: string }> = {
  "primary-light": {
    border: "hover:border-primary-light/50",
    text: "text-primary-light",
    bg: "bg-primary-light/10",
  },
  "accent-green": {
    border: "hover:border-accent-green/50",
    text: "text-accent-green",
    bg: "bg-accent-green/10",
  },
  "accent-orange": {
    border: "hover:border-accent-orange/50",
    text: "text-accent-orange",
    bg: "bg-accent-orange/10",
  },
  "accent-red": {
    border: "hover:border-accent-red/50",
    text: "text-accent-red",
    bg: "bg-accent-red/10",
  },
};

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
      <style>{`
        @keyframes puck-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes puck-slide {
          0%, 100% { left: 10%; }
          50% { left: 85%; }
        }
        @keyframes fade-in-up {
          from { opacity: 0; transform: translateY(24px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes glow-pulse {
          0%, 100% { box-shadow: 0 0 8px rgba(31,111,235,0.15); }
          50% { box-shadow: 0 0 24px rgba(31,111,235,0.35); }
        }
        .animate-fade-in-up {
          animation: fade-in-up 0.6s ease-out both;
        }
        .stagger-1 { animation-delay: 0.1s; }
        .stagger-2 { animation-delay: 0.2s; }
        .stagger-3 { animation-delay: 0.3s; }
        .stagger-4 { animation-delay: 0.4s; }
        .stagger-5 { animation-delay: 0.5s; }
      `}</style>

      {/* ─── Hero ─── */}
      <section
        className="relative overflow-hidden bg-gradient-to-br from-bg-card via-bg-gradient to-bg-card border-b border-border p-10 animate-fade-in-up"
        style={{ animation: "glow-pulse 3s infinite, fade-in-up 0.6s ease-out both" }}
      >
        {/* Ice rink pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.04] pointer-events-none"
          style={{
            backgroundImage: `
              radial-gradient(circle at 50% 50%, transparent 120px, rgba(31,111,235,0.3) 121px, rgba(31,111,235,0.3) 123px, transparent 124px),
              linear-gradient(to right, transparent 48%, rgba(248,81,73,0.5) 49%, rgba(248,81,73,0.5) 51%, transparent 52%),
              linear-gradient(to right, transparent 28%, rgba(31,111,235,0.4) 29%, rgba(31,111,235,0.4) 30%, transparent 31%),
              linear-gradient(to right, transparent 69%, rgba(31,111,235,0.4) 70%, rgba(31,111,235,0.4) 71%, transparent 72%)
            `,
            backgroundSize: "100% 100%",
          }}
        />

        {/* Crossed sticks watermark */}
        <svg
          className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 opacity-[0.03] pointer-events-none"
          viewBox="0 0 100 100"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <line x1="15" y1="85" x2="85" y2="15" strokeLinecap="round" />
          <line x1="85" y1="85" x2="15" y2="15" strokeLinecap="round" />
          <rect x="10" y="10" width="12" height="5" rx="1" transform="rotate(-45 16 12.5)" />
          <rect x="78" y="10" width="12" height="5" rx="1" transform="rotate(45 84 12.5)" />
        </svg>

        {/* Spinning puck */}
        <svg
          className="absolute top-6 right-8 w-14 h-14 text-text-muted/20"
          viewBox="0 0 50 50"
          style={{ animation: "puck-spin 20s linear infinite" }}
        >
          <ellipse cx="25" cy="25" rx="22" ry="22" fill="currentColor" />
          <ellipse cx="25" cy="25" rx="16" ry="16" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1" />
          <ellipse cx="25" cy="25" rx="8" ry="8" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
        </svg>

        <div className="relative z-10 max-w-2xl">
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
      <section className="p-8 animate-fade-in-up stagger-1">
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

      {/* ─── Feature Cards ─── */}
      <section className="px-8 pb-8 animate-fade-in-up stagger-2">
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
          Explore
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {FEATURE_CARDS.map((card) => {
            const a = ACCENT_CLASSES[card.accent];
            return (
              <Link
                key={card.href}
                href={card.href}
                className={`group block bg-bg-card border border-border rounded-xl p-5 transition-all hover:-translate-y-1 ${a.border}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`p-2 rounded-lg ${a.bg} ${a.text}`}>{card.icon}</div>
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
            );
          })}
        </div>
      </section>

      {/* ─── Hockey Rink Divider ─── */}
      <div className="px-8 py-4 animate-fade-in-up stagger-3">
        <div className="relative mx-auto max-w-xl h-16 rounded-[2rem] border border-text-muted/10 bg-bg-card/50 overflow-hidden">
          {/* Blue lines */}
          <div className="absolute top-0 bottom-0 left-[30%] w-px bg-primary/20" />
          <div className="absolute top-0 bottom-0 right-[30%] w-px bg-primary/20" />
          {/* Red center line */}
          <div className="absolute top-0 bottom-0 left-1/2 -translate-x-px w-0.5 bg-accent-red/25" />
          {/* Center circle */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 rounded-full border border-primary/15" />
          {/* Face-off dots */}
          <div className="absolute top-1/2 left-[20%] -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-accent-red/30" />
          <div className="absolute top-1/2 right-[20%] -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-accent-red/30" />
          <div className="absolute top-1/2 left-[40%] -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-accent-red/30" />
          <div className="absolute top-1/2 right-[40%] -translate-y-1/2 w-1.5 h-1.5 rounded-full bg-accent-red/30" />
          {/* Sliding puck */}
          <div
            className="absolute top-1/2 -translate-y-1/2 w-2.5 h-2.5 rounded-full bg-text-muted/40"
            style={{ animation: "puck-slide 8s ease-in-out infinite" }}
          />
        </div>
      </div>

      {/* ─── How It Works ─── */}
      <section className="px-8 py-8 animate-fade-in-up stagger-3">
        <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-6">
          How It Works
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative">
          {/* Dashed connecting lines (md+ only) */}
          <div className="hidden md:block absolute top-8 left-[33%] right-[67%] border-t border-dashed border-text-muted/20" />
          <div className="hidden md:block absolute top-8 left-[56%] right-[33%] border-t border-dashed border-text-muted/20" />

          {PIPELINE_STEPS.map((step) => (
            <div key={step.num} className="flex flex-col items-center text-center">
              <div className="relative w-16 h-16 rounded-full bg-bg-card border border-border flex items-center justify-center mb-3">
                <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-primary text-[10px] font-bold text-white flex items-center justify-center">
                  {step.num}
                </span>
                <div className="text-primary-light">{step.icon}</div>
              </div>
              <h3 className="text-base font-semibold text-text-bright mb-1">{step.title}</h3>
              <p className="text-sm text-text-muted leading-relaxed max-w-xs">{step.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ─── Top Scorers Ticker ─── */}
      {!scorersError && (
        <section className="px-8 pb-8 animate-fade-in-up stagger-4">
          <h2 className="text-sm font-semibold text-text-muted uppercase tracking-wider mb-4">
            Top Scorers
          </h2>
          <div className="bg-bg-card border border-border rounded-xl overflow-hidden">
            {scorers ? (
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
        </section>
      )}

      {/* ─── Footer CTA ─── */}
      <section className="px-8 py-10 border-t border-border text-center animate-fade-in-up stagger-5">
        <h2 className="text-xl font-bold text-text-bright mb-3">Ready to explore?</h2>
        <p className="text-text-muted mb-5 text-sm">
          Dive into the data and see which teams are trending toward the Cup.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-6 py-3 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-colors"
        >
          Get Started
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
          </svg>
        </Link>
      </section>
    </div>
  );
}
