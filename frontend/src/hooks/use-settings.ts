"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  batchUpsertCompanySettings,
  saveCompanyDefaults,
  saveScoringCriteriaDefaults,
  saveTeamMembersDefaults,
  saveCostItemsDefaults,
  createCostItem,
  createTeamMember,
  deleteCostItem,
  deleteTeamMember,
  getCriteria,
  getCompanySetting,
  listCostItems,
  listTeamMembers,
  updateCostItem,
  updateTeamMember,
  updateWeights,
  upsertCompanySetting,
} from "@/lib/api/settings";
import type {
  CompanySettingBatchUpsert,
  CompanySettingUpsert,
  CostItemCreate,
  CostItemDefaultsSave,
  CostItemUpdate,
  ScoringCriteriaDefaultsSave,
  TeamMemberCreate,
  TeamMemberDefaultsSave,
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

export function useSaveScoringCriteriaDefaults() {
  return useMutation({
    mutationFn: (data: ScoringCriteriaDefaultsSave) =>
      saveScoringCriteriaDefaults(data),
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

export function useBatchUpsertCompanySettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CompanySettingBatchUpsert) =>
      batchUpsertCompanySettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["company-setting"] });
    },
  });
}

export function useSaveCompanyDefaults() {
  return useMutation({
    mutationFn: (data: CompanySettingBatchUpsert) => saveCompanyDefaults(data),
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

export function useSaveTeamMembersDefaults() {
  return useMutation({
    mutationFn: (data: TeamMemberDefaultsSave) =>
      saveTeamMembersDefaults(data),
  });
}

export function useCostItems() {
  return useQuery({
    queryKey: ["cost-items"],
    queryFn: listCostItems,
  });
}

export function useCreateCostItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CostItemCreate) => createCostItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-items"] });
    },
  });
}

export function useUpdateCostItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: CostItemUpdate }) =>
      updateCostItem(itemId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-items"] });
    },
  });
}

export function useDeleteCostItem() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (itemId: string) => deleteCostItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cost-items"] });
    },
  });
}

export function useSaveCostItemsDefaults() {
  return useMutation({
    mutationFn: (data: CostItemDefaultsSave) => saveCostItemsDefaults(data),
  });
}
