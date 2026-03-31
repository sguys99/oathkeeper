import { get } from "./client";
import type { AgentLogResponse, AgentLogTreeResponse } from "./types";

export async function getAgentLogs(
  dealId: string,
): Promise<AgentLogResponse[]> {
  return get<AgentLogResponse[]>(`/api/deals/${dealId}/logs`);
}

export async function getAgentLogTree(
  dealId: string,
): Promise<AgentLogTreeResponse> {
  return get<AgentLogTreeResponse>(`/api/deals/${dealId}/logs?view=tree`);
}
