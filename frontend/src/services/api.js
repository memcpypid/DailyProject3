import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import NProgress from "nprogress";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

// Avoid infinite loops by tracking if refresh is processing
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(
  (config) => {
    NProgress.start();
    const token = localStorage.getItem("token");
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => {
    NProgress.done();
    // Return standard response structure
    return response;
  },
  async (error) => {
    NProgress.done();
    const originalRequest = error.config;
    const isAuthRoute =
      originalRequest.url.includes("/auth/login") ||
      originalRequest.url.includes("/auth/register") ||
      originalRequest.url.includes("/auth/refresh");

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !isAuthRoute
    ) {
      if (isRefreshing) {
        return new Promise(function (resolve, reject) {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers["Authorization"] = "Bearer " + token;
            return api(originalRequest);
          })
          .catch((err) => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const refreshToken = localStorage.getItem("refreshToken");
        if (!refreshToken) throw new Error("No refresh token available");

        const { data } = await axios.post(
          `${api.defaults.baseURL}/api/v1/auth/refresh`,
          {
            refresh_token: refreshToken,
          },
        );

        const newAccessToken = data.data.access_token;
        const newRefreshToken = data.data.refresh_token || refreshToken;

        // Save new tokens
        localStorage.setItem("token", newAccessToken);
        localStorage.setItem("refreshToken", newRefreshToken);

        api.defaults.headers.common["Authorization"] =
          `Bearer ${newAccessToken}`;
        originalRequest.headers["Authorization"] = `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        const authStore = useAuthStore();
        authStore.logout(); // Redirects to login
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);
/**
 * Endpoint to health check
 * @returns {Promise<import('axios').AxiosResponse<{success: boolean, message: string}>>}
 */
export const healthCheck = async () => {
  try {
    const data = await api.get("/api/v1/health");
    return data.message;
  } catch (err) {
    return err.response?.data?.message || err.message || "No Health Server";
  }
};
export default api;
