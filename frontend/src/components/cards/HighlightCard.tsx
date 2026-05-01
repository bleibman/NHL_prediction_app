interface HighlightCardProps {
  label: string;
  icon: string;
  title: string;
  subtitle?: string;
}

export default function HighlightCard({ label, icon, title, subtitle }: HighlightCardProps) {
  return (
    <div className="text-center p-6 mt-4 bg-gradient-to-br from-bg-card to-bg-gradient border border-border rounded-xl">
      <div className="text-xs font-semibold text-text-muted uppercase tracking-wider">
        {label}
      </div>
      <div className="text-4xl mt-2">{icon}</div>
      <div className="text-xl font-bold text-text-bright mt-2">{title}</div>
      {subtitle && (
        <div className="text-sm text-primary mt-1">{subtitle}</div>
      )}
    </div>
  );
}
