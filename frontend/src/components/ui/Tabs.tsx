"use client";

interface TabsProps {
  tabs: string[];
  activeTab: string;
  onChange: (tab: string) => void;
}

export default function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="flex gap-1 border-b border-border mb-6">
      {tabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onChange(tab)}
          className={`px-5 py-2.5 text-sm font-semibold rounded-t-lg transition-colors ${
            activeTab === tab
              ? "bg-bg-card text-text-bright border-b-2 border-primary"
              : "text-text-muted hover:text-text"
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
