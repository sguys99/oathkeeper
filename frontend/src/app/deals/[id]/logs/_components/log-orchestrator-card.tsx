"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { LogWorkerCard } from "./log-worker-card";
import { PromptViewer } from "./prompt-viewer";
import { formatDuration } from "./log-utils";
import { Clock } from "lucide-react";
import type { OrchestratorGroup } from "./log-tree-timeline";

const TOOL_NAME_LABELS: Record<string, string> = {
  run_deal_structuring: "Deal 구조화",
  run_scoring_analysis: "평가 기준 분석",
  run_resource_estimation: "리소스 추정",
  run_risk_analysis: "리스크 분석",
  run_similar_project_search: "유사 프로젝트 검색",
  run_final_verdict: "최종 판정",
  lookup_company_context: "회사 컨텍스트 조회",
};

function getGroupLabel(group: OrchestratorGroup): string {
  const { toolCalls } = group;
  if (toolCalls.length === 0) return "오케스트레이터 판단";

  const firstLabel =
    TOOL_NAME_LABELS[toolCalls[0].tool_name ?? ""] ??
    toolCalls[0].tool_name ??
    "오케스트레이터 판단";

  if (toolCalls.length === 1) return firstLabel;
  return `${firstLabel} 외 ${toolCalls.length - 1}건`;
}

interface LogOrchestratorCardProps {
  group: OrchestratorGroup;
  index: number;
}

export function LogOrchestratorCard({
  group,
  index,
}: LogOrchestratorCardProps) {
  const { reasoning, toolCalls } = group;

  // Collect all worker children from all tool calls
  const workersByToolCall = toolCalls.map((tc) => ({
    toolCall: tc,
    workers: tc.children.filter(
      (c) => c.step_type === "worker_start" || c.step_type === "worker_result",
    ),
  }));

  const hasError =
    toolCalls.some((tc) => !!tc.error) || (reasoning && !!reasoning.error);

  // Total duration = reasoning + all tool calls
  const totalDurationMs =
    (reasoning?.duration_ms ?? 0) +
    toolCalls.reduce((sum, tc) => sum + (tc.duration_ms ?? 0), 0);

  return (
    <div
      className="space-y-3"
      data-testid="orchestrator-card"
      data-step-type={toolCalls[0]?.step_type ?? reasoning?.step_type ?? "legacy"}
    >
      <div className="flex items-center gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-xs font-medium text-primary-foreground">
          {index + 1}
        </div>
        <h3 className="text-sm font-medium">{getGroupLabel(group)}</h3>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          {formatDuration(totalDurationMs)}
        </div>
        {hasError && <Badge variant="destructive">에러</Badge>}
      </div>

      {/* Reasoning section */}
      {reasoning?.raw_output && (
        <Card>
          <CardContent className="pt-4">
            <PromptViewer
              label="판단 근거 (LLM 출력)"
              content={reasoning.raw_output}
            />
            {reasoning.parsed_output && (
              <PromptViewer
                label="파싱된 판단 (JSON)"
                content={JSON.stringify(reasoning.parsed_output)}
                isJson
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* Tool call results (if no reasoning but tool calls have raw_output) */}
      {!reasoning &&
        toolCalls.length === 1 &&
        toolCalls[0].raw_output && (
          <Card>
            <CardContent className="pt-4">
              <PromptViewer
                label="판단 근거 (LLM 출력)"
                content={toolCalls[0].raw_output}
              />
              {toolCalls[0].parsed_output && (
                <PromptViewer
                  label="파싱된 판단 (JSON)"
                  content={JSON.stringify(toolCalls[0].parsed_output)}
                  isJson
                />
              )}
            </CardContent>
          </Card>
        )}

      {/* Worker cards from all tool calls */}
      {workersByToolCall.some((g) => g.workers.length > 0) && (
        <div className="ml-4 border-l-2 border-muted pl-4 space-y-3">
          {workersByToolCall.flatMap((g) =>
            g.workers.map((worker) => (
              <LogWorkerCard key={worker.id} node={worker} />
            )),
          )}
        </div>
      )}
    </div>
  );
}
