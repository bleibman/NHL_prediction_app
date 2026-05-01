interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
}

export default function StatCard({ label, value, sub }: StatCardProps) {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-5">
      <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-1.5">
        {label}
      </h4>
      <div className="text-3xl font-bold text-text-bright leading-tight">
        {value}
      </div>
      {sub && <p className="text-xs text-text-muted mt-1">{sub}</p>}
    </div>
  );
}
