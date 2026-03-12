"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createDeal, getDeal, listDeals, uploadDocument } from "@/lib/api/deals";
import type { DealCreate } from "@/lib/api/types";

export function useDeals(params?: {
  status?: string;
  offset?: number;
  limit?: number;
}) {
  return useQuery({
    queryKey: ["deals", params],
    queryFn: () => listDeals(params),
  });
}

export function useDeal(dealId: string | undefined) {
  return useQuery({
    queryKey: ["deal", dealId],
    queryFn: () => getDeal(dealId!),
    enabled: !!dealId,
  });
}

export function useDealPolling(dealId: string | undefined, enabled: boolean) {
  return useQuery({
    queryKey: ["deal", dealId],
    queryFn: () => getDeal(dealId!),
    enabled: !!dealId && enabled,
    refetchInterval: enabled ? 3000 : false,
  });
}

export function useCreateDeal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: DealCreate) => createDeal(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deals"] });
    },
  });
}

export function useUploadDocument() {
  return useMutation({
    mutationFn: ({ dealId, file }: { dealId: string; file: File }) =>
      uploadDocument(dealId, file),
  });
}
