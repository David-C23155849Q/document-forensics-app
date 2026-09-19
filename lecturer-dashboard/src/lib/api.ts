import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login/", { username, password });
  localStorage.setItem("access_token", data.access);
  localStorage.setItem("refresh_token", data.refresh);
  localStorage.setItem("user", JSON.stringify(data.user));
  return data.user;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
}

export function currentUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}

// ---- Types ----
export interface Assignment {
  id: number;
  title: string;
  assignment_code: string;
  course: string;
  status: string;
  deadline: string;
  start_time: string;
  submission_count: number;
}

export interface Submission {
  id: number;
  assignment: number;
  assignment_title: string;
  student: number;
  student_name: string;
  status: string;
  started_at: string | null;
  submitted_at: string | null;
  final_word_count: number;
}

export interface ForensicEventRow {
  id: number;
  event_type: string;
  timestamp: string;
  words_affected: number;
  characters_affected: number;
  classification_confidence: string;
  inserted_text?: string;
  deleted_text?: string;
  snapshot_before?: number;
  snapshot_after?: number;
}

export interface TimelineSession {
  session_id: number;
  start: string;
  end: string | null;
  active_seconds: number;
  idle_seconds: number;
  events: {
    id: number;
    type: string;
    timestamp: string;
    words_affected: number;
    characters_affected: number;
    confidence: string;
  }[];
}

export interface TimelineDay {
  date: string;
  sessions: TimelineSession[];
}

export interface AnalyticsResponse {
  word_count_trajectory: { timestamp: string; word_count: number }[];
  sessions: { session_count: number; total_active_seconds: number; total_idle_seconds: number };
  events: { counts_by_type: Record<string, number>; total_events: number; max_insertion_words: number; longest_inactivity_seconds: number };
}

// ---- Endpoints ----
export const Api = {
  assignments: () => api.get<Assignment[]>("/assignments/").then((r) => r.data),
  assignment: (id: number) => api.get<Assignment>(`/assignments/${id}/`).then((r) => r.data),
  submissionsForAssignment: (assignmentId: number) =>
    api.get<{ results: Submission[] } | Submission[]>(`/submissions/?assignment=${assignmentId}`).then((r) =>
      Array.isArray(r.data) ? r.data : r.data.results
    ),
  submission: (id: number) => api.get<Submission>(`/submissions/${id}/`).then((r) => r.data),
  timeline: (submissionId: number) => api.get<TimelineDay[]>(`/submissions/${submissionId}/timeline/`).then((r) => r.data),
  events: (submissionId: number, params?: Record<string, string>) =>
    api
      .get<{ results: ForensicEventRow[] } | ForensicEventRow[]>(`/submissions/${submissionId}/events/`, { params })
      .then((r) => (Array.isArray(r.data) ? r.data : r.data.results)),
  documentState: (submissionId: number, timestamp?: string) =>
    api
      .get(`/submissions/${submissionId}/document/state/`, { params: timestamp ? { timestamp } : {} })
      .then((r) => r.data),
  compare: (submissionId: number, before: number, after: number) =>
    api.get(`/submissions/${submissionId}/compare/`, { params: { before, after } }).then((r) => r.data),
  analytics: (submissionId: number) => api.get<AnalyticsResponse>(`/submissions/${submissionId}/analytics/`).then((r) => r.data),
  mlAnalysis: (submissionId: number) => api.get(`/submissions/${submissionId}/ml-analysis/`).then((r) => r.data),
  report: (submissionId: number) => api.get(`/submissions/${submissionId}/report/`).then((r) => r.data),
};
