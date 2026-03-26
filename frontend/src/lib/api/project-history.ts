import { get, post, del } from "./client";
import type {
  EmbedRequest,
  EmbedResponse,
  PageContentResponse,
  ProjectHistoryListResponse,
} from "./types";

export async function listProjectHistory(): Promise<ProjectHistoryListResponse> {
  return get<ProjectHistoryListResponse>("/api/project-history/");
}

export async function getPageContent(
  pageId: string,
): Promise<PageContentResponse> {
  return get<PageContentResponse>(`/api/project-history/${pageId}/content`);
}

export async function embedProjects(
  data?: EmbedRequest,
): Promise<EmbedResponse> {
  return post<EmbedResponse>("/api/project-history/embed", data ?? {});
}

export async function deleteEmbedding(pageId: string): Promise<void> {
  return del(`/api/project-history/${pageId}/embedding`);
}
