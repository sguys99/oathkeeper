import { get } from "./client";
import type { AgentLogResponse } from "./types";

export async function getAgentLogs(
  dealId: string,
): Promise<AgentLogResponse[]> {
  return get<AgentLogResponse[]>(`/api/deals/${dealId}/logs`);
}
