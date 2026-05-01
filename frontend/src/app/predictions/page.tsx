"use client";

import { useEffect, useState } from "react";
import { createColumnHelper } from "@tanstack/react-table";
import PageHeader from "@/components/layout/PageHeader";
import Select from "@/components/ui/Select";
import Button from "@/components/ui/Button";
import DataTable from "@/components/ui/DataTable";
import HighlightCard from "@/components/cards/HighlightCard";
import PlotlyChart from "@/components/charts/PlotlyChart";
import { formatSeason } from "@/lib/utils";
import { getPredictionSeasons, runPredictions } from "@/lib/api";
import type { PredictionRow } from "@/lib/types";

const predCol = createColumnHelper<PredictionRow>();
const predColumns = [
  predCol.accessor("rank", { header: "Rank" }),
  predCol.accessor("abbreviation", { header: "Team" }),
  predCol.accessor("team_name", { header: "Name" }),
  predCol.accessor("cup_probability", {
    header: "Win %",
    cell: (info) => `${info.getValue().toFixed(1)}%`,
  }),
];

export default function PredictionsPage() {
  const [seasons, setSeasons] = useState<number[]>([]);
  const [selectedSeason, setSelectedSeason] = useState<number>(0);
  const [predictions, setPredictions] = useState<PredictionRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);

  useEffect(() => {
    getPredictionSeasons().then((s) => {
      setSeasons(s);
      if (s.length > 0) setSelectedSeason(s[0]);
      setPageLoading(false);
    });
  }, []);

  const handleRun = async () => {
    setLoading(true);
    setPredictions([]);
    try {
      const results = await runPredictions(selectedSeason);
      setPredictions(results);
    } catch (e) {
      console.error("Prediction failed:", e);
    } finally {
      setLoading(false);
    }
  };

  if (pageLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  const top = predictions.length > 0 ? predictions[0] : null;
  const chartData = predictions.slice(0, 16).reverse();

  return (
    <>
      <PageHeader
        title="Stanley Cup Predictions"
        subtitle="ML-powered bracket simulation using historical performance data"
      />

      <div className="flex items-end gap-4 mb-8">
        <div>
          <label className="block text-xs font-semibold text-text-muted uppercase mb-1.5">
            Predict for season
          </label>
          <Select
            options={seasons.map((s) => ({ value: s.toString(), label: formatSeason(s) }))}
            value={selectedSeason.toString()}
            onChange={(v) => setSelectedSeason(Number(v))}
          />
        </div>
        <Button
          label={loading ? "Training model..." : "Run Prediction"}
          onClick={handleRun}
          loading={loading}
        />
      </div>

      {top && (
        <>
          <div className="max-w-md mx-auto mb-8">
            <HighlightCard
              label="Predicted Favorite"
              icon="\uD83C\uDFC6"
              title={top.team_name}
              subtitle={`${top.abbreviation} \u2014 ${top.cup_probability.toFixed(1)}% chance`}
            />
          </div>

          <h2 className="text-lg font-bold text-text-bright mb-4">Win Probabilities</h2>
          <PlotlyChart
            data={[
              {
                x: chartData.map((d) => d.cup_probability),
                y: chartData.map((d) => d.abbreviation),
                type: "bar",
                orientation: "h",
                marker: {
                  color: chartData.map((d) => d.cup_probability),
                  colorscale: [
                    [0, "#21262d"],
                    [0.5, "#1f6feb"],
                    [1, "#58a6ff"],
                  ],
                },
                text: chartData.map((d) => `${d.cup_probability.toFixed(1)}%`),
                textposition: "outside",
                textfont: { color: "#c9d1d9", size: 12 },
              },
            ]}
            layout={{
              xaxis: {
                title: "Win Probability (%)",
                gridcolor: "#21262d",
                zerolinecolor: "#21262d",
              },
              yaxis: { title: "", gridcolor: "#21262d", zerolinecolor: "#21262d" },
              showlegend: false,
            }}
            height={Math.max(400, chartData.length * 32)}
          />

          <hr className="border-border my-8" />

          <h2 className="text-lg font-bold text-text-bright mb-4">All Teams</h2>
          <DataTable columns={predColumns} data={predictions} />
        </>
      )}
    </>
  );
}
