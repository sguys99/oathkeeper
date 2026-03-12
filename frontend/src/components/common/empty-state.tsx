import { cn } from "@/lib/utils";
import { Inbox } from "lucide-react";

export function EmptyState({
  message = "데이터가 없습니다",
  className,
}: {
  message?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col items-center justify-center gap-2 py-12 text-muted-foreground", className)}>
      <Inbox className="h-10 w-10" />
      <p className="text-sm">{message}</p>
    </div>
  );
}
