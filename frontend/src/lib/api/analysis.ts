import { get, post } from "./client";
import type { AnalysisResponse, AnalysisTriggerResponse } from "./types";

export async function triggerAnalysis(
  dealId: string,
  workflowType?: string,
): Promise<AnalysisTriggerResponse> {
  const body = workflowType ? { workflow_type: workflowType } : undefined;
  return post<AnalysisTriggerResponse>(`/api/deals/${dealId}/analyze`, body);
}

export async function getAnalysis(
  dealId: string,
): Promise<AnalysisResponse> {
  return get<AnalysisResponse>(`/api/deals/${dealId}/analysis`);
}
