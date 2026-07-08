import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const TOKEN_KEY = 'estoque_access_token';
export const REFRESH_KEY = 'estoque_refresh_token';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Attach the bearer token to every request.
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem(REFRESH_KEY);
  if (!refreshToken) return null;
  try {
    const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_KEY, data.refresh_token);
    return data.access_token as string;
  } catch {
    return null;
  }
}

// Transparently refresh the access token once on 401, then retry.
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    const isAuthCall = original?.url?.includes('/auth/');
    if (error.response?.status === 401 && original && !original._retry && !isAuthCall) {
      original._retry = true;
      refreshing = refreshing || refreshAccessToken();
      const newToken = await refreshing;
      refreshing = null;
      if (newToken) {
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      }
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_KEY);
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

/**
 * Resolve a backend-relative asset path (e.g. "/uploads/products/x.jpg") to a
 * URL the browser can load. When the SPA and API share an origin (dev proxy or
 * nginx), paths stay relative; when the API lives on another origin (typical on
 * a managed PaaS, via VITE_API_BASE_URL), the API origin is prefixed.
 */
export function assetUrl(path?: string | null): string | undefined {
  if (!path) return undefined;
  if (/^https?:\/\//.test(path)) return path;
  const apiOrigin = BASE_URL.replace(/\/api\/v\d+\/?$/, '');
  return /^https?:\/\//.test(apiOrigin) ? `${apiOrigin}${path}` : path;
}

/** Extract a human-readable message from an API error. */
export function apiErrorMessage(error: unknown, fallback = 'Ocorreu um erro'): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    if (detail) return detail;
    if (error.message) return error.message;
  }
  return fallback;
}
