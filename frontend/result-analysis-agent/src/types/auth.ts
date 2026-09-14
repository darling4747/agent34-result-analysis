// ─── Auth Types ──────────────────────────────────────────────────────────────

export type UserRole =
  | 'PLATFORM_ADMIN'
  | 'DEAN'
  | 'HOD'
  | 'FACULTY'
  | 'IQAC'
  | 'MANAGEMENT'
  | 'AUDITOR';

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  department: string | null;
  permissions: string[];
  mfa_enabled?: boolean;
}

export interface LoginResult {
  mfa_required?: boolean;
  mfa_token?: string;
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  must_change_password?: boolean;
  user: AuthUser;
}

export interface MfaSetupData {
  secret: string;
  provisioning_uri: string;
  qr_code_data_uri: string;
  recovery_codes: string[];
}

export interface MfaStatusData {
  mfa_enabled: boolean;
  mfa_enabled_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  must_change_password: boolean;
  user: AuthUser;
}

export interface AuthState {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  mustChangePassword: boolean;
  isLoading: boolean;
}
