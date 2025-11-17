import axios from "axios";

// Safely compute API base. Fall back to localhost:8000 for dev if NEXT_PUBLIC_API_BASE is missing.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// Axios for pre-csrf
const preCSRFF = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: true,
});

// Axios for csrf
const csrfRoute = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    "X-CSRFToken": "csrftoken",
  },
});

// This works for session based CSRF tokens
csrfRoute.interceptors.request.use(async (config) => {
  const token = await preCSRFF.get("/csrf/");

  config.headers["X-CSRFToken"] = token.data.csrfToken;
  return config;
});

export default csrfRoute;
