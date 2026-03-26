import { get, put } from "./client";
import type { PromptResponse, PromptUpdateRequest } from "./types";

export async function listPrompts(): Promise<PromptResponse[]> {
  return get<PromptResponse[]>("/api/prompts");
}

export async function getPrompt(name: string): Promise<PromptResponse> {
  return get<PromptResponse>(`/api/prompts/${name}`);
}

export async function updatePrompt(
  name: string,
  data: PromptUpdateRequest,
): Promise<PromptResponse> {
  return put<PromptResponse>(`/api/prompts/${name}`, data);
}
