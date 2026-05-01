interface InfoBoxProps {
  text: string;
}

export default function InfoBox({ text }: InfoBoxProps) {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-5 mb-6">
      <p className="text-sm text-text">{text}</p>
    </div>
  );
}
