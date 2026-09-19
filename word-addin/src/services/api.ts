import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("addin_access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login/", { username, password });
  localStorage.setItem("addin_access_token", data.access);
  localStorage.setItem("addin_user", JSON.stringify(data.user));
  return data.user;
}

export function isAuthenticated() {
  return !!localStorage.getItem("addin_access_token");
}

export function currentUser() {
  const raw = localStorage.getItem("addin_user");
  return raw ? JSON.parse(raw) : null;
}

export async function fetchMyAssignments() {
  const { data } = await api.get("/assignments/");
  return data.results ?? data;
}

export async function startSubmission(assignmentId: number) {
  const { data } = await api.post("/submissions/", { assignment: assignmentId });
  return data;
}

export async function startSession(submissionId: number) {
  const { data } = await api.post("/sessions/start/", {
    submission_id: submissionId,
    device_info: navigator.userAgent,
  });
  return data;
}

export async function endSession(sessionId: number, activeSeconds: number, idleSeconds: number) {
  const { data } = await api.post(`/sessions/${sessionId}/end/`, {
    active_seconds: activeSeconds,
    idle_seconds: idleSeconds,
  });
  return data;
}

export async function syncBatch(payload: {
  submission_id: number;
  events: Record<string, unknown>[];
  snapshots: Record<string, unknown>[];
  client_timestamp: string;
  client_id: string;
}) {
  const { data } = await api.post("/sync/", payload);
  return data;
}

export async function submitAssignment(submissionId: number) {
  const { data } = await api.post(`/submissions/${submissionId}/submit/`);
  return data;
}
