import axios from 'axios';

const defaultBaseUrl = import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1';
const rawBaseUrl = (import.meta.env.VITE_API_URL || defaultBaseUrl).replace(/\/$/, '');
export const API_V1_BASE_URL = rawBaseUrl.endsWith('/api') ? `${rawBaseUrl}/v1` : rawBaseUrl;
export const AUTH_GOOGLE_URL = `${API_V1_BASE_URL}/auth/google`;

export const apiClient = axios.create({
  baseURL: API_V1_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
});

apiClient.interceptors.request.use((config) => {
  const raw = localStorage.getItem('maillens-store');
  if (raw) {
    try {
      const store = JSON.parse(raw);
      const token = store?.state?.user?.id;
      if (token) config.headers['Authorization'] = `Bearer ${token}`;
    } catch (_) {}
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('maillens-store');
      window.location.href = '/';
    }
    return Promise.reject(err);
  }
);
