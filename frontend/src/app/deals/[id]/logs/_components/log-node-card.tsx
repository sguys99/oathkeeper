"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { PromptViewer } from "./prompt-viewer";
import { formatDuration, LEGACY_NODE_LABELS } from "./log-utils";
import { Clock, AlertCircle } from "lucide-react";
import type { AgentLogResponse } from "@/lib/api/types";

interface LogNodeCardProps {
  log: AgentLogResponse;
}

export function LogNodeCard({ log }: LogNodeCardProps) {
  const label = LEGACY_NODE_LABELS[log.node_name] ?? log.node_name;
  const hasError = !!log.error;

  return (
    <Card className={hasError ? "border-destructive/50" : ""}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{label}</CardTitle>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3.5 w-3.5" />
              {formatDuration(log.duration_ms)}
            </div>
            <Badge variant={hasError ? "destructive" : "secondary"}>
              {hasError ? "에러" : "성공"}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-0">
        {hasError && (
          <div className="mb-3 flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{log.error}</span>
          </div>
        )}

        <PromptViewer label="시스템 프롬프트" content={log.system_prompt} />
        <PromptViewer label="유저 프롬프트" content={log.user_prompt} />
        <PromptViewer label="LLM 원본 출력" content={log.raw_output} />
        {log.parsed_output && (
          <PromptViewer
            label="파싱된 결과 (JSON)"
            content={JSON.stringify(log.parsed_output)}
            isJson
          />
        )}
      </CardContent>
    </Card>
  );
}
