"use client";

import { useQuery } from "@tanstack/react-query";
import { getMe } from "@/lib/api/users";
import { getUserEmail } from "@/lib/api/client";

export function useCurrentUser() {
  const email = getUserEmail();
  return useQuery({
    queryKey: ["currentUser", email],
    queryFn: getMe,
    enabled: !!email,
    staleTime: 5 * 60 * 1000,
  });
}
