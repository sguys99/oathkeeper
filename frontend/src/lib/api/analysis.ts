import { get, post } from "./client";
import type { AnalysisResponse, AnalysisTriggerResponse } from "./types";

export async function triggerAnalysis(
  dealId: string,
): Promise<AnalysisTriggerResponse> {
  return post<AnalysisTriggerResponse>(`/api/deals/${dealId}/analyze`);
}

export async function getAnalysis(
  dealId: string,
): Promise<AnalysisResponse> {
  return get<AnalysisResponse>(`/api/deals/${dealId}/analysis`);
}
