"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { PromptViewer } from "./prompt-viewer";
import { formatDuration } from "./log-utils";
import {
  Brain,
  Wrench,
  Eye,
  Clock,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import type { AgentLogTreeNode } from "@/lib/api/types";

const STEP_CONFIG: Record<
  string,
  { icon: typeof Brain; label: string; color: string }
> = {
  reasoning: { icon: Brain, label: "추론", color: "text-blue-500" },
  tool_call: { icon: Wrench, label: "도구 호출", color: "text-amber-500" },
  observation: { icon: Eye, label: "관찰 결과", color: "text-green-500" },
};

interface LogReActStepProps {
  step: AgentLogTreeNode;
}

export function LogReActStep({ step }: LogReActStepProps) {
  const [expanded, setExpanded] = useState(false);
  const config = STEP_CONFIG[step.step_type ?? ""] ?? {
    icon: Brain,
    label: step.step_type ?? "unknown",
    color: "text-muted-foreground",
  };
  const Icon = config.icon;
  const hasError = !!step.error;

  const summaryLabel =
    step.step_type === "tool_call" && step.tool_name
      ? `${config.label}: ${step.tool_name}`
      : config.label;

  return (
    <div className="rounded-md border bg-card">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-3 text-sm hover:bg-muted/50"
      >
        <div className="flex items-center gap-2">
          {expanded ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          <Icon className={`h-4 w-4 ${config.color}`} />
          <span className="font-medium">{summaryLabel}</span>
          {step.step_index !== null && (
            <Badge variant="outline" className="text-xs">
              #{step.step_index}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3 w-3" />
            {formatDuration(step.duration_ms)}
          </span>
          {hasError && <Badge variant="destructive">에러</Badge>}
        </div>
      </button>

      {expanded && (
        <div className="border-t px-3 pb-3">
          {hasError && (
            <div className="mt-2 rounded-md bg-destructive/10 p-2 text-xs text-destructive">
              {step.error}
            </div>
          )}
          <PromptViewer label="입력 / 프롬프트" content={step.user_prompt} />
          <PromptViewer label="원본 출력" content={step.raw_output} />
          {step.parsed_output && (
            <PromptViewer
              label="파싱된 결과 (JSON)"
              content={JSON.stringify(step.parsed_output)}
              isJson
            />
          )}
        </div>
      )}
    </div>
  );
}
