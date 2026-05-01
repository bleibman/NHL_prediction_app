import { cn } from "@/lib/utils";

interface ButtonProps {
  label: string;
  onClick: () => void;
  loading?: boolean;
  variant?: "primary" | "secondary";
  className?: string;
}

export default function Button({
  label,
  onClick,
  loading = false,
  variant = "primary",
  className = "",
}: ButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={cn(
        "px-5 py-2.5 rounded-lg font-semibold text-sm transition-colors disabled:opacity-50",
        variant === "primary"
          ? "bg-primary text-white hover:bg-primary-hover"
          : "bg-bg-card border border-border text-text hover:bg-bg-gradient",
        className
      )}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {label}
        </span>
      ) : (
        label
      )}
    </button>
  );
}
