import axios from "axios";

// Safely compute API base.
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

// Route to fetch data from django
const djangoRoute = axios.create({
  baseURL: `${API_BASE}/api`,
  withCredentials: true,
});

export default djangoRoute;
