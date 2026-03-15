"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { listPrompts, getPrompt, updatePrompt } from "@/lib/api/prompts";
import type { PromptUpdateRequest } from "@/lib/api/types";

export function usePrompts() {
  return useQuery({
    queryKey: ["prompts"],
    queryFn: listPrompts,
  });
}

export function usePrompt(name: string) {
  return useQuery({
    queryKey: ["prompts", name],
    queryFn: () => getPrompt(name),
    enabled: !!name,
  });
}

export function useUpdatePrompt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      name,
      data,
    }: {
      name: string;
      data: PromptUpdateRequest;
    }) => updatePrompt(name, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      queryClient.invalidateQueries({
        queryKey: ["prompts", variables.name],
      });
    },
  });
}
