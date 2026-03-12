"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { getAnalysis, triggerAnalysis } from "@/lib/api/analysis";

export function useAnalysis(dealId: string | undefined) {
  return useQuery({
    queryKey: ["analysis", dealId],
    queryFn: () => getAnalysis(dealId!),
    enabled: !!dealId,
    retry: false,
  });
}

export function useTriggerAnalysis() {
  return useMutation({
    mutationFn: (dealId: string) => triggerAnalysis(dealId),
  });
}
