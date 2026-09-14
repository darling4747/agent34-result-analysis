import apiClient from './client';
import type { AuthUser, LoginResult, MfaSetupData, MfaStatusData } from '@/types/auth';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export async function login(req: LoginRequest): Promise<{ success: boolean; data: LoginResult }> {
  const resp = await apiClient.post('/api/auth/login', req);
  return resp.data;
}

export async function changeInitialPassword(
  req: ChangePasswordRequest,
): Promise<{ success: boolean; data: { access_token: string; refresh_token: string; must_change_password: boolean } }> {
  const resp = await apiClient.post('/api/auth/change-initial-password', req);
  return resp.data;
}

export async function logout(): Promise<void> {
  try {
    await apiClient.post('/api/auth/logout', {});
  } catch {
    // Best-effort — always clear local state
  }
}

export async function getMe(): Promise<{ success: boolean; data: AuthUser }> {
  const resp = await apiClient.get('/api/auth/me');
  return resp.data;
}

// ─── MFA API endpoints ────────────────────────────────────────────────────────

export async function verifyMfaLogin(mfa_token: string, totp_code?: string, recovery_code?: string): Promise<{ success: boolean; data: LoginResult }> {
  const resp = await apiClient.post('/api/auth/mfa/verify', { mfa_token, totp_code, recovery_code });
  return resp.data;
}

export async function getMfaStatus(): Promise<{ success: boolean; data: MfaStatusData }> {
  const resp = await apiClient.get('/api/auth/mfa/status');
  return resp.data;
}

export async function setupMfa(): Promise<{ success: boolean; data: MfaSetupData }> {
  const resp = await apiClient.post('/api/auth/mfa/setup', {});
  return resp.data;
}

export async function verifyMfaSetup(totp_code: string, recovery_codes: string[]) {
  const resp = await apiClient.post('/api/auth/mfa/verify-setup', { totp_code, recovery_codes });
  return resp.data;
}

export async function disableMfa(password: string) {
  const resp = await apiClient.post('/api/auth/mfa/disable', { password });
  return resp.data;
}

export async function regenerateMfaRecoveryCodes(): Promise<{ success: boolean; data: { recovery_codes: string[] } }> {
  const resp = await apiClient.post('/api/auth/mfa/regenerate-recovery-codes', {});
  return resp.data;
}

// ─── Admin user management ───────────────────────────────────────────────────

export interface CreateUserRequest {
  email: string;
  full_name: string;
  role: string;
  department?: string;
  faculty_id?: number;
}

export async function createUser(req: CreateUserRequest) {
  const resp = await apiClient.post('/api/auth/admin/users', req);
  return resp.data;
}

export async function listUsers() {
  const resp = await apiClient.get('/api/auth/admin/users');
  return resp.data;
}

export async function deactivateUser(userId: number) {
  const resp = await apiClient.patch(`/api/auth/admin/users/${userId}/deactivate`, {});
  return resp.data;
}

export async function activateUser(userId: number) {
  const resp = await apiClient.patch(`/api/auth/admin/users/${userId}/activate`, {});
  return resp.data;
}

export async function forcePasswordReset(userId: number) {
  const resp = await apiClient.post(`/api/auth/admin/users/${userId}/force-reset`, {});
  return resp.data;
}

export async function adminResetMfa(userId: number) {
  const resp = await apiClient.post(`/api/auth/admin/users/${userId}/mfa/reset`, {});
  return resp.data;
}

export async function getAuditLogs() {
  const resp = await apiClient.get('/api/auth/audit-logs');
  return resp.data;
}