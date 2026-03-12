"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createTeamMember,
  deleteTeamMember,
  getCriteria,
  getCompanySetting,
  listTeamMembers,
  updateTeamMember,
  updateWeights,
  upsertCompanySetting,
} from "@/lib/api/settings";
import type {
  CompanySettingUpsert,
  TeamMemberCreate,
  TeamMemberUpdate,
  WeightUpdateRequest,
} from "@/lib/api/types";

export function useCriteria() {
  return useQuery({
    queryKey: ["criteria"],
    queryFn: getCriteria,
  });
}

export function useUpdateWeights() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: WeightUpdateRequest) => updateWeights(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["criteria"] });
    },
  });
}

export function useCompanySetting(key: string) {
  return useQuery({
    queryKey: ["company-setting", key],
    queryFn: () => getCompanySetting(key),
    retry: false,
  });
}

export function useUpsertCompanySetting() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CompanySettingUpsert) => upsertCompanySetting(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["company-setting", variables.key],
      });
    },
  });
}

export function useTeamMembers() {
  return useQuery({
    queryKey: ["team-members"],
    queryFn: listTeamMembers,
  });
}

export function useCreateTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TeamMemberCreate) => createTeamMember(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-members"] });
    },
  });
}

export function useUpdateTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      memberId,
      data,
    }: {
      memberId: string;
      data: TeamMemberUpdate;
    }) => updateTeamMember(memberId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-members"] });
    },
  });
}

export function useDeleteTeamMember() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (memberId: string) => deleteTeamMember(memberId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["team-members"] });
    },
  });
}
