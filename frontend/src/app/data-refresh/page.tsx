"use client";

import { useState, useRef } from "react";
import PageHeader from "@/components/layout/PageHeader";
import InfoBox from "@/components/cards/InfoBox";
import Button from "@/components/ui/Button";
import ProgressBar from "@/components/ui/ProgressBar";
import { startRefresh } from "@/lib/api";
import { formatSeason } from "@/lib/utils";

interface StepStatus {
  label: string;
  status: "pending" | "running" | "done" | "error";
  error?: string;
}

export default function DataRefreshPage() {
  const [seasonInput, setSeasonInput] = useState(20242025);
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<StepStatus[]>([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [totalSteps, setTotalSteps] = useState(6);
  const [done, setDone] = useState(false);
  const cancelRef = useRef<(() => void) | null>(null);

  const handleRefresh = (seasonId: number | null) => {
    setRunning(true);
    setDone(false);
    setSteps([]);
    setCurrentStep(0);

    cancelRef.current = startRefresh(seasonId, (event) => {
      if (event.done) {
        setDone(true);
        setRunning(false);
        setCurrentStep(totalSteps);
        return;
      }

      const step = event.step as number;
      const total = event.total as number;
      const label = event.label as string;
      const status = event.status as string;

      setTotalSteps(total);
      setCurrentStep(status === "done" || status === "error" ? step : step - 1);

      setSteps((prev) => {
        const copy = [...prev];
        const idx = step - 1;
        copy[idx] = {
          label,
          status: status as StepStatus["status"],
          error: event.error as string | undefined,
        };
        return copy;
      });

      if (status === "error") {
        setRunning(false);
      }
    });
  };

  return (
    <>
      <PageHeader title="Data Refresh" subtitle="Fetch the latest data from the NHL API and SeatGeek" />

      <InfoBox text="The ETL pipeline fetches teams, season stats, game results, playoff series, and player stats from the NHL API, plus ticket prices from SeatGeek, and upserts them into the database." />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-bright mb-2">Refresh All Seasons</h3>
          <p className="text-xs text-text-muted mb-4">
            Re-fetches data for all 20 seasons (2005&ndash;25). Games fetch is slow.
          </p>
          <Button
            label={running ? "Running..." : "Refresh All"}
            onClick={() => handleRefresh(null)}
            loading={running}
          />
        </div>

        <div className="bg-bg-card border border-border rounded-xl p-6">
          <h3 className="text-sm font-bold text-text-bright mb-2">Refresh Single Season</h3>
          <input
            type="number"
            value={seasonInput}
            onChange={(e) => setSeasonInput(Number(e.target.value))}
            min={20052006}
            max={20252026}
            step={10001}
            className="w-full bg-bg border border-border rounded-lg px-3 py-2 text-sm text-text mb-2 focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <p className="text-xs text-text-muted mb-4">
            Will refresh {formatSeason(seasonInput)} only.
          </p>
          <Button
            label={running ? "Running..." : "Refresh Season"}
            onClick={() => handleRefresh(seasonInput)}
            loading={running}
          />
        </div>
      </div>

      {(steps.length > 0 || done) && (
        <div className="bg-bg-card border border-border rounded-xl p-6">
          <ProgressBar value={currentStep} max={totalSteps} label="ETL Pipeline Progress" />

          <div className="mt-4 space-y-2">
            {steps.map((step, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="w-5 text-center">
                  {step.status === "done" && (
                    <span className="text-accent-green">&#10003;</span>
                  )}
                  {step.status === "running" && (
                    <span className="animate-spin inline-block h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                  )}
                  {step.status === "error" && (
                    <span className="text-accent-red">&#10007;</span>
                  )}
                  {step.status === "pending" && (
                    <span className="text-text-muted">&bull;</span>
                  )}
                </span>
                <span className={step.status === "done" ? "text-text" : step.status === "error" ? "text-accent-red" : "text-text-muted"}>
                  {step.label}
                </span>
                {step.error && (
                  <span className="text-xs text-accent-red ml-2">({step.error})</span>
                )}
              </div>
            ))}
          </div>

          {done && (
            <p className="mt-4 text-sm text-accent-green font-semibold">
              Data refresh complete. Reload the page to see updated data.
            </p>
          )}
        </div>
      )}
    </>
  );
}
