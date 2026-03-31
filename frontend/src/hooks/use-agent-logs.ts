"use client";

import { useQuery } from "@tanstack/react-query";
import { getAgentLogs, getAgentLogTree } from "@/lib/api/agent-logs";

export function useAgentLogs(dealId: string | undefined) {
  return useQuery({
    queryKey: ["agent-logs", dealId],
    queryFn: () => getAgentLogs(dealId!),
    enabled: !!dealId,
  });
}

export function useAgentLogsPolling(
  dealId: string | undefined,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["agent-logs", dealId],
    queryFn: () => getAgentLogs(dealId!),
    enabled: !!dealId && enabled,
    refetchInterval: enabled ? 3000 : false,
  });
}

export function useAgentLogTree(dealId: string | undefined) {
  return useQuery({
    queryKey: ["agent-log-tree", dealId],
    queryFn: () => getAgentLogTree(dealId!),
    enabled: !!dealId,
  });
}

export function useAgentLogTreePolling(
  dealId: string | undefined,
  enabled: boolean,
) {
  return useQuery({
    queryKey: ["agent-log-tree", dealId],
    queryFn: () => getAgentLogTree(dealId!),
    enabled: !!dealId && enabled,
    refetchInterval: enabled ? 3000 : false,
  });
}
