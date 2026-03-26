import { del, get, post, upload } from "./client";
import type { DealCreate, DealListResponse, DealResponse } from "./types";

export async function createDeal(data: DealCreate): Promise<DealResponse> {
  return post<DealResponse>("/api/deals/", data);
}

export async function listDeals(params?: {
  status?: string;
  created_by?: string;
  offset?: number;
  limit?: number;
}): Promise<DealListResponse> {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set("status", params.status);
  if (params?.created_by) searchParams.set("created_by", params.created_by);
  if (params?.offset !== undefined)
    searchParams.set("offset", String(params.offset));
  if (params?.limit !== undefined)
    searchParams.set("limit", String(params.limit));
  const qs = searchParams.toString();
  return get<DealListResponse>(`/api/deals/${qs ? `?${qs}` : ""}`);
}

export async function getDeal(dealId: string): Promise<DealResponse> {
  return get<DealResponse>(`/api/deals/${dealId}`);
}

export async function listImportedNotionPageIds(): Promise<string[]> {
  return get<string[]>("/api/deals/notion-page-ids");
}

export async function deleteDeal(dealId: string): Promise<void> {
  return del(`/api/deals/${dealId}`);
}

export async function uploadDocument(
  dealId: string,
  file: File,
): Promise<DealResponse> {
  return upload<DealResponse>(`/api/deals/${dealId}/upload`, file);
}
