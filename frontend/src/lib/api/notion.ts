import { get, post } from "./client";
import type {
  NotionDealListResponse,
  NotionSaveRequest,
  NotionSaveResponse,
} from "./types";

export async function listNotionDeals(): Promise<NotionDealListResponse> {
  return get<NotionDealListResponse>("/api/notion/deals");
}

export async function saveToNotion(
  dealId: string,
  data?: NotionSaveRequest,
): Promise<NotionSaveResponse> {
  return post<NotionSaveResponse>(
    `/api/deals/${dealId}/save-to-notion`,
    data ?? { include_report: true },
  );
}
