import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { getMe, login as apiLogin, logout as apiLogout } from '@/api/authApi';
import type { AuthState, LoginResult } from '@/types/auth';

const TOKEN_KEY = 'agent34_token';
const REFRESH_KEY = 'agent34_refresh';

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<LoginResult>;
  completeMfaLogin: (result: LoginResult) => void;
  logout: () => Promise<void>;
  clearAuth: () => void;
  hasPermission: (perm: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    mustChangePassword: false,
    isLoading: true,
  });

  // On mount, restore session from localStorage
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      setState((s) => ({ ...s, isLoading: false }));
      return;
    }
    getMe()
      .then((res) => {
        setState({
          user: res.data,
          token,
          isAuthenticated: true,
          mustChangePassword: false,
          isLoading: false,
        });
      })
      .catch(() => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
        setState({ user: null, token: null, isAuthenticated: false, mustChangePassword: false, isLoading: false });
      });
  }, []);

  const login = useCallback(async (email: string, password: string): Promise<LoginResult> => {
    const res = await apiLogin({ email, password });
    if (res.data.mfa_required) {
      return res.data;
    }
    const { access_token, refresh_token, must_change_password, user } = res.data;
    if (access_token) localStorage.setItem(TOKEN_KEY, access_token);
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
    setState({
      user,
      token: access_token ?? null,
      isAuthenticated: true,
      mustChangePassword: !!must_change_password,
      isLoading: false,
    });
    return res.data;
  }, []);

  const completeMfaLogin = useCallback((result: LoginResult) => {
    const { access_token, refresh_token, must_change_password, user } = result;
    if (access_token) localStorage.setItem(TOKEN_KEY, access_token);
    if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token);
    setState({
      user,
      token: access_token ?? null,
      isAuthenticated: true,
      mustChangePassword: !!must_change_password,
      isLoading: false,
    });
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setState({ user: null, token: null, isAuthenticated: false, mustChangePassword: false, isLoading: false });
  }, []);

  const clearAuth = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setState({ user: null, token: null, isAuthenticated: false, mustChangePassword: false, isLoading: false });
  }, []);

  const hasPermission = useCallback((perm: string): boolean => {
    return state.user?.permissions.includes(perm) ?? false;
  }, [state.user]);

  const value: AuthContextValue = { ...state, login, completeMfaLogin, logout, clearAuth, hasPermission };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
