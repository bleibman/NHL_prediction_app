interface PageHeaderProps {
  title: string;
  subtitle: string;
}

export default function PageHeader({ title, subtitle }: PageHeaderProps) {
  return (
    <div className="pb-6 mb-6 border-b border-border">
      <h1 className="text-2xl font-bold text-text-bright">{title}</h1>
      <p className="text-sm text-text-muted mt-1">{subtitle}</p>
    </div>
  );
}
