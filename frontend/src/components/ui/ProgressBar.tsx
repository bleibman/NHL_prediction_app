interface ProgressBarProps {
  value: number;
  max: number;
  label?: string;
}

export default function ProgressBar({ value, max, label }: ProgressBarProps) {
  const pct = max > 0 ? (value / max) * 100 : 0;

  return (
    <div className="w-full">
      {label && (
        <p className="text-sm text-text-muted mb-2">{label}</p>
      )}
      <div className="w-full bg-bg-card border border-border rounded-full h-3 overflow-hidden">
        <div
          className="h-full bg-primary rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className="text-xs text-text-muted mt-1 text-right">
        {value}/{max}
      </p>
    </div>
  );
}
