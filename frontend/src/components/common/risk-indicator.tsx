import { cn } from "@/lib/utils";
import type { RiskLevel } from "@/lib/api/types";

const config: Record<RiskLevel, { label: string; dotClass: string; textClass: string }> = {
  CRITICAL: {
    label: "CRITICAL",
    dotClass: "bg-red-700",
    textClass: "text-red-900",
  },
  HIGH: {
    label: "HIGH",
    dotClass: "bg-red-500",
    textClass: "text-red-700",
  },
  MEDIUM: {
    label: "MEDIUM",
    dotClass: "bg-amber-500",
    textClass: "text-amber-700",
  },
  LOW: {
    label: "LOW",
    dotClass: "bg-green-500",
    textClass: "text-green-700",
  },
};

export function RiskIndicator({
  level,
  className,
}: {
  level: RiskLevel;
  className?: string;
}) {
  const c = config[level];
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", c.textClass, className)}>
      <span className={cn("h-2 w-2 rounded-full", c.dotClass)} />
      {c.label}
    </span>
  );
}
