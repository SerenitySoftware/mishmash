"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import {
  apiFetch,
  clearToken,
  getStoredUser,
  setStoredUser,
  setToken,
  type TokenResponse,
  type UserOut,
} from "@/lib/api";

interface AuthContextType {
  user: UserOut | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, name: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  refreshUser: async () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const u = await apiFetch<UserOut>("/api/auth/me");
      setUser(u);
      setStoredUser(u);
    } catch {
      setUser(null);
      clearToken();
    }
  }, []);

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) {
      setUser(stored);
      refreshUser().finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const resp = await apiFetch<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setToken(resp.access_token);
    setUser(resp.user);
    setStoredUser(resp.user);
  };

  const register = async (email: string, username: string, name: string, password: string) => {
    const resp = await apiFetch<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, username, name, password }),
    });
    setToken(resp.access_token);
    setUser(resp.user);
    setStoredUser(resp.user);
  };

  const logout = () => {
    clearToken();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
