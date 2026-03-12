import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Verdict } from "@/lib/api/types";

const config: Record<
  Verdict,
  { label: string; className: string }
> = {
  go: {
    label: "Go",
    className: "bg-green-100 text-green-700 border-green-200 hover:bg-green-100",
  },
  conditional_go: {
    label: "조건부 Go",
    className: "bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-100",
  },
  no_go: {
    label: "No-Go",
    className: "bg-red-100 text-red-700 border-red-200 hover:bg-red-100",
  },
  pending: {
    label: "보류",
    className: "bg-gray-100 text-gray-500 border-gray-200 hover:bg-gray-100",
  },
};

export function VerdictBadge({
  verdict,
  className,
}: {
  verdict: Verdict | null;
  className?: string;
}) {
  if (!verdict) return null;
  const c = config[verdict];
  return (
    <Badge variant="outline" className={cn(c.className, className)}>
      {c.label}
    </Badge>
  );
}
