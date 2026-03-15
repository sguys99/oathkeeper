"use client";

import { LogNodeCard } from "./log-node-card";
import type { AgentLogResponse } from "@/lib/api/types";

const PARALLEL_NODES = new Set([
  "scoring",
  "resource_estimation",
  "risk_analysis",
  "similar_project",
]);

interface LogTimelineProps {
  logs: AgentLogResponse[];
}

export function LogTimeline({ logs }: LogTimelineProps) {
  // Group logs into phases
  const dealStructuring = logs.find((l) => l.node_name === "deal_structuring");
  const parallelLogs = logs.filter((l) => PARALLEL_NODES.has(l.node_name));
  const finalVerdict = logs.find(
    (l) => l.node_name === "final_verdict" || l.node_name === "hold_verdict",
  );

  return (
    <div className="space-y-6">
      {/* Phase 1: Deal Structuring */}
      {dealStructuring && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
              1
            </div>
            <h3 className="text-sm font-medium text-muted-foreground">
              딜 구조화 단계
            </h3>
          </div>
          <LogNodeCard log={dealStructuring} />
        </div>
      )}

      {/* Phase 2: Parallel Analysis */}
      {parallelLogs.length > 0 && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
              2
            </div>
            <h3 className="text-sm font-medium text-muted-foreground">
              병렬 분석 단계
            </h3>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {parallelLogs.map((log) => (
              <LogNodeCard key={log.id} log={log} />
            ))}
          </div>
        </div>
      )}

      {/* Phase 3: Final Verdict */}
      {finalVerdict && (
        <div>
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
              3
            </div>
            <h3 className="text-sm font-medium text-muted-foreground">
              최종 판정 단계
            </h3>
          </div>
          <LogNodeCard log={finalVerdict} />
        </div>
      )}
    </div>
  );
}
