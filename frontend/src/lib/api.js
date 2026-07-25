import axios from "axios";

export const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "";

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  withCredentials: true,
});

// Session expired or never existed — bounce to login instead of leaving
// every page to fail silently. Skip /auth/me itself since ProtectedRoute
// already handles that check explicitly.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && error.config?.url !== "/auth/me") {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
