"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listNotionDeals, saveToNotion } from "@/lib/api/notion";
import type { NotionSaveRequest } from "@/lib/api/types";

export function useNotionDeals() {
  return useQuery({
    queryKey: ["notion-deals"],
    queryFn: listNotionDeals,
  });
}

export function useSaveToNotion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      dealId,
      data,
    }: {
      dealId: string;
      data?: NotionSaveRequest;
    }) => saveToNotion(dealId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["analysis", variables.dealId],
      });
    },
  });
}
