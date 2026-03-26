import { get, post } from "./client";
import type { UserCreate, UserResponse } from "./types";

export async function createUser(data: UserCreate): Promise<UserResponse> {
  return post<UserResponse>("/api/users/", data);
}

export async function getMe(): Promise<UserResponse> {
  return get<UserResponse>("/api/users/me");
}
