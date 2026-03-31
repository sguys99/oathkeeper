"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LogReActStep } from "./log-react-step";
import { PromptViewer } from "./prompt-viewer";
import { getNodeLabel, formatDuration } from "./log-utils";
import { ChevronDown, ChevronRight, Clock } from "lucide-react";
import type { AgentLogTreeNode } from "@/lib/api/types";

interface LogWorkerCardProps {
  node: AgentLogTreeNode;
}

export function LogWorkerCard({ node }: LogWorkerCardProps) {
  const [open, setOpen] = useState(false);
  const label = getNodeLabel(node);
  const hasError = !!node.error;
  const isInProgress = !node.completed_at && !hasError;
  const reactSteps = node.children
    .filter(
      (c) =>
        c.step_type === "reasoning" ||
        c.step_type === "tool_call" ||
        c.step_type === "observation",
    )
    .sort((a, b) => (a.step_index ?? 0) - (b.step_index ?? 0));
  const stepCount = reactSteps.length;

  return (
    <Card className={hasError ? "border-destructive/50" : ""}>
      <CardHeader
        className="cursor-pointer pb-3 hover:bg-muted/50"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {open ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
            <CardTitle className="text-base">{label}</CardTitle>
            {stepCount > 0 && (
              <span className="text-xs text-muted-foreground">
                ({stepCount}개 스텝)
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3.5 w-3.5" />
              {formatDuration(node.duration_ms)}
            </div>
            <Badge
              variant={
                hasError
                  ? "destructive"
                  : isInProgress
                    ? "outline"
                    : "secondary"
              }
            >
              {hasError ? "에러" : isInProgress ? "진행 중" : "성공"}
            </Badge>
          </div>
        </div>
      </CardHeader>

      {open && (
        <CardContent className="space-y-0 pt-0">
          {hasError && (
            <div className="mb-3 flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
              <span>{node.error}</span>
            </div>
          )}

          <PromptViewer label="시스템 프롬프트" content={node.system_prompt} />
          <PromptViewer label="유저 프롬프트" content={node.user_prompt} />

          {reactSteps.length > 0 && (
            <div className="mt-3 space-y-2">
              <p className="text-xs font-medium text-muted-foreground">
                ReAct 루프
              </p>
              {reactSteps.map((step) => (
                <LogReActStep key={step.id} step={step} />
              ))}
            </div>
          )}

          <PromptViewer label="워커 최종 출력" content={node.raw_output} />
          {node.parsed_output && (
            <PromptViewer
              label="파싱된 결과 (JSON)"
              content={JSON.stringify(node.parsed_output)}
              isJson
            />
          )}
        </CardContent>
      )}
    </Card>
  );
}
