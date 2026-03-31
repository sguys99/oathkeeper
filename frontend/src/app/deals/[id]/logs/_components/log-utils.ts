import type { AgentLogTreeNode, AgentLogTreeResponse } from "@/lib/api/types";

export function isLegacyLogTree(tree: AgentLogTreeResponse): boolean {
  return tree.logs.every((log) => log.step_type === null);
}

export function formatDuration(ms: number | null): string {
  if (ms === null) return "-";
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

const WORKER_LABELS: Record<string, string> = {
  deal_structuring_worker: "딜 구조화 워커",
  scoring_worker: "스코어링 워커",
  resource_worker: "리소스 추정 워커",
  risk_worker: "리스크 분석 워커",
  similar_project_worker: "유사 프로젝트 워커",
  verdict_worker: "최종 판정 워커",
};

export const LEGACY_NODE_LABELS: Record<string, string> = {
  deal_structuring: "딜 구조화",
  scoring: "스코어링",
  resource_estimation: "리소스 추정",
  risk_analysis: "리스크 분석",
  similar_project: "유사 프로젝트",
  final_verdict: "최종 판정",
  hold_verdict: "보류 판정",
};

export function getNodeLabel(node: AgentLogTreeNode): string {
  if (
    node.step_type === "orchestrator_decision" ||
    node.step_type === "orchestrator_reasoning" ||
    node.step_type === "orchestrator_tool_call"
  ) {
    return "오케스트레이터 판단";
  }
  if (node.step_type === "worker_start" || node.step_type === "worker_result") {
    return (
      WORKER_LABELS[node.worker_name ?? ""] ?? node.worker_name ?? node.node_name
    );
  }
  if (node.step_type === "tool_call") {
    return `도구 호출: ${node.tool_name ?? "unknown"}`;
  }
  if (node.step_type === "reasoning") return "추론";
  if (node.step_type === "observation") return "관찰 결과";
  return LEGACY_NODE_LABELS[node.node_name] ?? node.node_name;
}
