"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LogWorkerCard } from "./log-worker-card";
import { PromptViewer } from "./prompt-viewer";
import { formatDuration } from "./log-utils";
import { GitBranch, Clock } from "lucide-react";
import type { AgentLogTreeNode } from "@/lib/api/types";

interface LogOrchestratorCardProps {
  node: AgentLogTreeNode;
  index: number;
}

export function LogOrchestratorCard({
  node,
  index,
}: LogOrchestratorCardProps) {
  const workerChildren = node.children.filter(
    (c) => c.step_type === "worker_start" || c.step_type === "worker_result",
  );
  const hasError = !!node.error;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
          {index + 1}
        </div>
        <GitBranch className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-medium">오케스트레이터 판단</h3>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          {formatDuration(node.duration_ms)}
        </div>
        {hasError && <Badge variant="destructive">에러</Badge>}
      </div>

      <Card>
        <CardContent className="pt-4">
          <PromptViewer label="판단 근거 (LLM 출력)" content={node.raw_output} />
          {node.parsed_output && (
            <PromptViewer
              label="파싱된 판단 (JSON)"
              content={JSON.stringify(node.parsed_output)}
              isJson
            />
          )}
        </CardContent>
      </Card>

      {workerChildren.length > 0 && (
        <div className="ml-4 border-l-2 border-muted pl-4 space-y-3">
          {workerChildren.map((worker) => (
            <LogWorkerCard key={worker.id} node={worker} />
          ))}
        </div>
      )}
    </div>
  );
}
