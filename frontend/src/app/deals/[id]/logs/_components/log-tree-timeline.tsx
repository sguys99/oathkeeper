"use client";

import { LogOrchestratorCard } from "./log-orchestrator-card";
import { LogWorkerCard } from "./log-worker-card";
import { LogNodeCard } from "./log-node-card";
import { formatDuration } from "./log-utils";
import { Clock } from "lucide-react";
import type { AgentLogTreeNode, AgentLogTreeResponse } from "@/lib/api/types";

interface LogTreeTimelineProps {
  tree: AgentLogTreeResponse;
}

export function LogTreeTimeline({ tree }: LogTreeTimelineProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>총 {tree.total_count}개 스텝</span>
        <span className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" />
          총 소요: {formatDuration(tree.total_duration_ms)}
        </span>
      </div>

      {tree.logs.map((node, index) => (
        <RootNode key={node.id} node={node} index={index} />
      ))}
    </div>
  );
}

function RootNode({
  node,
  index,
}: {
  node: AgentLogTreeNode;
  index: number;
}) {
  if (
    node.step_type === "orchestrator_decision" ||
    node.step_type === "orchestrator_reasoning" ||
    node.step_type === "orchestrator_tool_call"
  ) {
    return <LogOrchestratorCard node={node} index={index} />;
  }
  if (node.step_type === "worker_start" || node.step_type === "worker_result") {
    return <LogWorkerCard node={node} />;
  }
  return <LogNodeCard log={node} />;
}
