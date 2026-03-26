import { del, get, post, put } from "./client";
import type {
  CompanySettingBatchUpsert,
  CompanySettingResponse,
  CompanySettingUpsert,
  CostItemCreate,
  CostItemDefaultsSave,
  CostItemResponse,
  CostItemUpdate,
  ScoringCriteriaDefaultsSave,
  ScoringCriteriaResponse,
  TeamMemberCreate,
  TeamMemberDefaultsSave,
  TeamMemberResponse,
  TeamMemberUpdate,
  WeightUpdateRequest,
} from "./types";

// Scoring criteria
export async function getCriteria(): Promise<ScoringCriteriaResponse[]> {
  return get<ScoringCriteriaResponse[]>("/api/settings/criteria");
}

export async function updateWeights(
  data: WeightUpdateRequest,
): Promise<ScoringCriteriaResponse[]> {
  return put<ScoringCriteriaResponse[]>("/api/settings/criteria/weights", data);
}

export async function saveScoringCriteriaDefaults(
  data: ScoringCriteriaDefaultsSave,
): Promise<{ message: string }> {
  return put<{ message: string }>("/api/settings/criteria/save-defaults", data);
}

// Company settings
export async function getCompanySetting(
  key: string,
): Promise<CompanySettingResponse> {
  return get<CompanySettingResponse>(`/api/settings/company/${key}`);
}

export async function upsertCompanySetting(
  data: CompanySettingUpsert,
): Promise<CompanySettingResponse> {
  return put<CompanySettingResponse>("/api/settings/company", data);
}

export async function batchUpsertCompanySettings(
  data: CompanySettingBatchUpsert,
): Promise<CompanySettingResponse[]> {
  return put<CompanySettingResponse[]>("/api/settings/company/batch", data);
}

export async function saveCompanyDefaults(
  data: CompanySettingBatchUpsert,
): Promise<{ message: string }> {
  return put<{ message: string }>("/api/settings/company/save-defaults", data);
}

// Team members
export async function listTeamMembers(): Promise<TeamMemberResponse[]> {
  return get<TeamMemberResponse[]>("/api/settings/team-members");
}

export async function createTeamMember(
  data: TeamMemberCreate,
): Promise<TeamMemberResponse> {
  return post<TeamMemberResponse>("/api/settings/team-members", data);
}

export async function updateTeamMember(
  memberId: string,
  data: TeamMemberUpdate,
): Promise<TeamMemberResponse> {
  return put<TeamMemberResponse>(
    `/api/settings/team-members/${memberId}`,
    data,
  );
}

export async function deleteTeamMember(memberId: string): Promise<void> {
  return del(`/api/settings/team-members/${memberId}`);
}

export async function saveTeamMembersDefaults(
  data: TeamMemberDefaultsSave,
): Promise<{ message: string }> {
  return put<{ message: string }>(
    "/api/settings/team-members/save-defaults",
    data,
  );
}

// Cost items
export async function listCostItems(): Promise<CostItemResponse[]> {
  return get<CostItemResponse[]>("/api/settings/cost-items");
}

export async function createCostItem(
  data: CostItemCreate,
): Promise<CostItemResponse> {
  return post<CostItemResponse>("/api/settings/cost-items", data);
}

export async function updateCostItem(
  itemId: string,
  data: CostItemUpdate,
): Promise<CostItemResponse> {
  return put<CostItemResponse>(`/api/settings/cost-items/${itemId}`, data);
}

export async function deleteCostItem(itemId: string): Promise<void> {
  return del(`/api/settings/cost-items/${itemId}`);
}

export async function saveCostItemsDefaults(
  data: CostItemDefaultsSave,
): Promise<{ message: string }> {
  return put<{ message: string }>(
    "/api/settings/cost-items/save-defaults",
    data,
  );
}
