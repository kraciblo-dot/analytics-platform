import axios from 'axios';

// Create a configured axios instance
export const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
  // CRITICAL: This tells the browser to always send the HttpOnly cookie
  withCredentials: true, 
});

// We need a variable to prevent infinite refresh loops
let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request Interceptor: Attach the access token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response Interceptor: Catch 401s and try to refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If the error is 401 and we haven't already tried to retry this request...
    if (error.response?.status === 401 && !originalRequest._retry) {
      // If we are hitting an auth endpoint, don't intercept, just let it fail
      if (originalRequest.url.includes('/auth/login') || originalRequest.url.includes('/auth/refresh')) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Ping our secure refresh endpoint
        const response = await api.post('/auth/refresh');
        const { access_token } = response.data;
        
        // Save the new short-lived token
        localStorage.setItem('access_token', access_token);
        
        api.defaults.headers.common['Authorization'] = 'Bearer ' + access_token;
        originalRequest.headers['Authorization'] = 'Bearer ' + access_token;
        
        processQueue(null, access_token);
        
        // Retry the original failed request!
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        // If the refresh token is ALSO dead (e.g., 7 days passed), force logout
        localStorage.removeItem('access_token');
        window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);