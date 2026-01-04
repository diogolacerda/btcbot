import axios from 'axios';

// Runtime environment variables injected by Docker entrypoint
// These placeholders (__VITE_*__) are replaced by sed at container startup
const API_URL = '__VITE_API_URL__';
const API_BASE_PATH = '__VITE_API_BASE_PATH__';

export const axiosInstance = axios.create({
  baseURL: `${API_URL}${API_BASE_PATH}`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for JWT token injection
axiosInstance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
