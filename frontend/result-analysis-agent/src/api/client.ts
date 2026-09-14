import axios, { AxiosError, type AxiosInstance, type AxiosResponse } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
const TOKEN_KEY = 'agent34_token';

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT from localStorage on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers['Authorization'] = `Bearer ${token}`;
  return config;
});

// Normalise errors; redirect on 401; surface PASSWORD_CHANGE_REQUIRED on 403
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError<{ detail?: string | { msg: string }[]; message?: string }>) => {
    if (!error.response) {
      return Promise.reject(new ApiError('Network error — unable to reach the server.', 0));
    }

    const { status, data } = error.response;
    let message = 'An unexpected error occurred.';

    if (typeof data?.detail === 'string') {
      message = data.detail;
    } else if (Array.isArray(data?.detail)) {
      message = (data.detail as { msg: string }[]).map((d) => d.msg).join('; ');
    } else if (data?.message) {
      message = data.message as string;
    } else {
      message = HTTP_ERROR_MESSAGES[status] ?? message;
    }

    // Auto-redirect on expired / invalid token
    if (status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }

    return Promise.reject(new ApiError(message, status));
  },
);

export class ApiError extends Error {
  readonly statusCode: number;
  constructor(message: string, statusCode: number) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
  }
  get isNetworkError() { return this.statusCode === 0; }
  get isNotFound()     { return this.statusCode === 404; }
  get isUnauthorized() { return this.statusCode === 401; }
  get isForbidden()    { return this.statusCode === 403; }
  get isPasswordChangeRequired() {
    return this.statusCode === 403 && this.message === 'PASSWORD_CHANGE_REQUIRED';
  }
  get isConflict()     { return this.statusCode === 409; }
  get isValidation()   { return this.statusCode === 422; }
  get isServerError()  { return this.statusCode >= 500; }
}

const HTTP_ERROR_MESSAGES: Record<number, string> = {
  400: 'Bad request — please check the submitted data.',
  401: 'Authentication required. Please log in.',
  403: 'You do not have permission to perform this action.',
  404: 'The requested resource was not found.',
  409: 'A conflict occurred — this record may already exist.',
  422: 'Validation failed — please check the submitted data.',
  500: 'Server error — please try again later.',
  502: 'Server is temporarily unavailable.',
  503: 'Service unavailable — please try again later.',
};

export default apiClient;
