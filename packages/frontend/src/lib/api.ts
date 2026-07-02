// Thin fetch wrapper around the FitVise REST API.
// In single_user mode no token is required; in multi_user the app stores a
// bearer JWT obtained from /auth/login and attaches it automatically.

export const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  ""
);

const TOKEN_KEY = "fitvise.token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T = unknown>(
  path: string,
  options: RequestInit & { json?: unknown } = {}
): Promise<T> {
  const { json, headers, ...rest } = options;
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(headers ?? {}),
    },
    body: json !== undefined ? JSON.stringify(json) : rest.body,
  });

  if (res.status === 204) return undefined as T;
  const text = await res.text();
  const data = text ? JSON.parse(text) : undefined;
  if (!res.ok) {
    const detail = (data && (data.detail || data.error)) || res.statusText;
    throw new ApiError(res.status, typeof detail === "string" ? detail : "Request failed");
  }
  return data as T;
}

// ---- Endpoint helpers ----------------------------------------------
export const Api = {
  health: () => api<HealthResponse>("/health"),
  me: () => api<User>("/api/v1/auth/me"),
  login: (email: string, password: string) =>
    api<TokenResponse>("/api/v1/auth/login", { method: "POST", json: { email, password } }),
  register: (name: string, email: string, password: string) =>
    api<TokenResponse>("/api/v1/auth/register", {
      method: "POST",
      json: { name, email, password },
    }),

  profile: () => api<Profile>("/api/v1/profile"),
  onboardingStatus: () => api<OnboardingStatus>("/api/v1/profile/onboarding-status"),

  currentProgramme: () => api<Programme>("/api/v1/programme/current"),

  workouts: (params = "") => api<WorkoutLog[]>(`/api/v1/workouts${params}`),
  createWorkout: (body: unknown) =>
    api<WorkoutLog>("/api/v1/workouts", { method: "POST", json: body }),

  diet: (params = "") => api<DietLog[]>(`/api/v1/diet${params}`),
  createDiet: (body: unknown) => api<DietLog>("/api/v1/diet", { method: "POST", json: body }),
  deleteDiet: (id: string) => api(`/api/v1/diet/${id}`, { method: "DELETE" }),

  injuries: () => api<InjuryLog[]>("/api/v1/journal/injuries"),
  createInjury: (body: unknown) =>
    api<InjuryLog>("/api/v1/journal/injuries", { method: "POST", json: body }),

  metrics: (params = "") => api<BodyMetrics[]>(`/api/v1/metrics${params}`),
  createMetrics: (body: unknown) =>
    api<BodyMetrics>("/api/v1/metrics", { method: "POST", json: body }),

  checkins: () => api<CheckIn[]>("/api/v1/checkins"),

  notifications: (unreadOnly = false) =>
    api<NotificationItem[]>(`/api/v1/notifications?unread_only=${unreadOnly}`),
  unreadCount: () => api<{ unread: number }>("/api/v1/notifications/unread-count"),
  markRead: (id: string) =>
    api(`/api/v1/notifications/${id}/read`, { method: "POST" }),
  markAllRead: () => api("/api/v1/notifications/read-all", { method: "POST" }),
  deleteNotification: (id: string) =>
    api(`/api/v1/notifications/${id}`, { method: "DELETE" }),
  clearRead: () => api<{ deleted: number }>("/api/v1/notifications/read", { method: "DELETE" }),
  notificationPrefs: () => api<NotificationPrefs>("/api/v1/notifications/preferences"),
  updateNotificationPrefs: (body: Partial<NotificationPrefs>) =>
    api<NotificationPrefs>("/api/v1/notifications/preferences", { method: "PUT", json: body }),
  vapidKey: () => api<{ public_key: string | null; enabled: boolean }>(
    "/api/v1/notifications/vapid-public-key"
  ),
  subscribePush: (body: unknown) =>
    api("/api/v1/notifications/push/subscribe", { method: "POST", json: body }),
  testNotification: () => api("/api/v1/notifications/test", { method: "POST" }),
};

// ---- Types (mirror backend schemas) --------------------------------
export interface HealthResponse {
  status: string;
  version: string;
  auth_mode: "single_user" | "multi_user" | "managed";
  db: { type: string; connected: boolean };
  oauth: { enabled: boolean; issuer: string | null };
  webpush: { enabled: boolean };
}
export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}
export interface User {
  id: string;
  name: string;
  age: number | null;
  gender: string | null;
  email: string | null;
  is_admin: boolean;
  weight_unit: string;
  measurement_unit: string;
  onboarding_completed_at: string | null;
}
export interface Profile {
  goal_type: string | null;
  training_modality: string | null;
  current_weight: number | null;
  height: number | null;
  target_weight: number | null;
  target_waist: number | null;
  diet_type: string | null;
  dietary_restrictions: string | null;
  training_days_per_week: number | null;
  preferred_activities: string[] | null;
  equipment_available: string[] | null;
  session_length_preference: number | null;
  gym_access_type: string | null;
  injuries_notes: string | null;
}
export interface OnboardingStatus {
  onboarding_completed: boolean;
  completed_at: string | null;
  missing_fields: string[];
}
export interface Programme {
  id: string;
  name: string;
  total_weeks: number;
  current_week: number;
  goal_type: string | null;
  sessions: ProgrammeSession[];
}
export interface ProgrammeSession {
  id: string;
  week_number: number;
  day_of_week: number | null;
  session_type: string;
  label: string | null;
  exercises: ExerciseItem[];
  warmup: AccessoryItem[] | null;
  cooldown: AccessoryItem[] | null;
}
export interface ExerciseItem {
  id: string;
  name: string;
  sets: number | null;
  reps_min: number | null;
  reps_max: number | null;
  reps_raw: string | null;
  rest_seconds: number | null;
  form_notes: string | null;
}
export interface AccessoryItem {
  name: string;
  reps: string | null;
  rest_seconds: number | null;
  notes: string | null;
}
export interface WorkoutLog {
  id: string;
  date: string;
  notes: string | null;
  sets: {
    exercise_name: string;
    set_number?: number;
    weight: number | null;
    reps: number | null;
  }[];
}
export interface InjuryLog {
  id: string;
  date: string;
  body_area: string;
  injury_type: string | null;
  severity: number | null;
  context: string | null;
  note: string | null;
  logged_at: string;
}
export interface DietLog {
  id: string;
  date: string;
  meal_slot: string;
  description: string | null;
  protein_quality: string | null;
  flags: string[] | null;
  logged_at: string;
}
export interface BodyMetrics {
  id: string;
  logged_at: string;
  weight: number | null;
  waist_cm: number | null;
}
export interface CheckIn {
  id: string;
  date: string;
  ai_summary: string | null;
  weight_at_checkin: number | null;
  waist_at_checkin: number | null;
}
export interface NotificationItem {
  id: string;
  type: string;
  title: string;
  body: string | null;
  data: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
}
export interface NotificationPrefs {
  inapp_enabled: boolean;
  webpush_enabled: boolean;
  daily_reminder_enabled: boolean;
  daily_reminder_time: string;
  missed_workout_enabled: boolean;
  workout_updated_enabled: boolean;
  checkin_enabled: boolean;
}
