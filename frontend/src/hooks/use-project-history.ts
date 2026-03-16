"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  listProjectHistory,
  getPageContent,
  embedProjects,
} from "@/lib/api/project-history";
import type { EmbedRequest } from "@/lib/api/types";

export function useProjectHistory() {
  return useQuery({
    queryKey: ["project-history"],
    queryFn: listProjectHistory,
  });
}

export function usePageContent(pageId: string | null) {
  return useQuery({
    queryKey: ["project-history", "content", pageId],
    queryFn: () => getPageContent(pageId!),
    enabled: !!pageId,
  });
}

export function useEmbedProjects() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data?: EmbedRequest) => embedProjects(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["project-history"] });
    },
  });
}
