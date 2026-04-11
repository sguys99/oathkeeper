"use client";

import { LogOrchestratorCard } from "./log-orchestrator-card";
import { LogWorkerCard } from "./log-worker-card";
import { LogNodeCard } from "./log-node-card";
import { formatDuration } from "./log-utils";
import { Clock } from "lucide-react";
import type { AgentLogTreeNode, AgentLogTreeResponse } from "@/lib/api/types";

/** A group of orchestrator reasoning + subsequent tool call(s). */
export interface OrchestratorGroup {
  reasoning?: AgentLogTreeNode;
  toolCalls: AgentLogTreeNode[];
}

interface LogTreeTimelineProps {
  tree: AgentLogTreeResponse;
}

export function LogTreeTimeline({ tree }: LogTreeTimelineProps) {
  const grouped = groupRootNodes(tree.logs);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>총 {tree.total_count}개 스텝</span>
        <span className="flex items-center gap-1">
          <Clock className="h-3.5 w-3.5" />
          총 소요: {formatDuration(tree.total_duration_ms)}
        </span>
      </div>

      {grouped.map((item, index) => {
        if ("toolCalls" in item) {
          return (
            <LogOrchestratorCard
              key={item.toolCalls[0]?.id ?? `group-${index}`}
              group={item}
              index={index}
            />
          );
        }
        const node = item as AgentLogTreeNode;
        if (
          node.step_type === "worker_start" ||
          node.step_type === "worker_result"
        ) {
          return <LogWorkerCard key={node.id} node={node} />;
        }
        return <LogNodeCard key={node.id} log={node} />;
      })}
    </div>
  );
}

/**
 * Group root-level orchestrator nodes: merge each REASONING with its
 * subsequent TOOL_CALL(s) into a single {@link OrchestratorGroup}.
 *
 * Consecutive TOOL_CALL entries (parallel invocations) are grouped together.
 * A standalone REASONING at the end (final orchestrator thought) is wrapped
 * in a group with an empty toolCalls array.
 */
function groupRootNodes(
  logs: AgentLogTreeNode[],
): (OrchestratorGroup | AgentLogTreeNode)[] {
  const result: (OrchestratorGroup | AgentLogTreeNode)[] = [];
  let pendingReasoning: AgentLogTreeNode | undefined;

  for (const node of logs) {
    if (node.step_type === "orchestrator_reasoning") {
      // Flush any previous pending reasoning as a standalone group
      if (pendingReasoning) {
        result.push({ reasoning: pendingReasoning, toolCalls: [] });
      }
      pendingReasoning = node;
      continue;
    }

    if (node.step_type === "orchestrator_tool_call") {
      const last = result[result.length - 1];
      if (pendingReasoning) {
        // Start a new group with the pending reasoning
        result.push({ reasoning: pendingReasoning, toolCalls: [node] });
        pendingReasoning = undefined;
      } else if (last && "toolCalls" in last) {
        // Extend existing group (parallel tool calls after first)
        last.toolCalls.push(node);
      } else {
        // Tool call with no preceding reasoning
        result.push({ toolCalls: [node] });
      }
      continue;
    }

    // Non-orchestrator node — flush pending reasoning first
    if (pendingReasoning) {
      result.push({ reasoning: pendingReasoning, toolCalls: [] });
      pendingReasoning = undefined;
    }
    result.push(node);
  }

  // Trailing reasoning (e.g., final orchestrator thought)
  if (pendingReasoning) {
    result.push({ reasoning: pendingReasoning, toolCalls: [] });
  }

  return result;
}
