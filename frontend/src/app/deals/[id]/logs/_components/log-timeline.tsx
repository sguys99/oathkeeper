"use client";

import type { AgentLogTreeResponse } from "@/lib/api/types";
import { isLegacyLogTree } from "./log-utils";
import { LogLegacyTimeline } from "./log-legacy-timeline";
import { LogTreeTimeline } from "./log-tree-timeline";

interface LogTimelineProps {
  tree: AgentLogTreeResponse;
}

export function LogTimeline({ tree }: LogTimelineProps) {
  if (isLegacyLogTree(tree)) {
    return <LogLegacyTimeline logs={tree.logs} />;
  }
  return <LogTreeTimeline tree={tree} />;
}
