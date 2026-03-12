"use client";

import { setUserEmail } from "@/lib/api/client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

interface UserContextValue {
  email: string | null;
  setEmail: (email: string | null) => void;
}

const UserContext = createContext<UserContextValue>({
  email: null,
  setEmail: () => {},
});

export function UserProvider({ children }: { children: ReactNode }) {
  const [email, setEmailState] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("user_email");
    }
    return null;
  });

  useEffect(() => {
    setUserEmail(email);
    if (email) {
      localStorage.setItem("user_email", email);
    } else {
      localStorage.removeItem("user_email");
    }
  }, [email]);

  return (
    <UserContext.Provider value={{ email, setEmail: setEmailState }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
