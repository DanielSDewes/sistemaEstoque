import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { authApi } from '@/api/endpoints';
import { REFRESH_KEY, TOKEN_KEY } from '@/api/client';
import type { User } from '@/api/types';

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (code: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setLoading(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (username: string, password: string) => {
    const data = await authApi.login(username, password);
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_KEY, data.refresh_token);
    setUser(data.user);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_KEY);
      setUser(null);
    }
  };

  const permissionCodes = useMemo(() => {
    if (!user) return new Set<string>();
    if (user.is_superuser) return new Set<string>(['*']);
    return new Set(user.role?.permissions?.map((p) => p.code) ?? []);
  }, [user]);

  const hasPermission = (code: string) =>
    permissionCodes.has('*') || permissionCodes.has(code);

  const value = useMemo(
    () => ({ user, loading, login, logout, hasPermission }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [user, loading, permissionCodes],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
