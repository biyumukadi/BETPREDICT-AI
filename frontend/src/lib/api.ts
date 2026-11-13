const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export type Fixture = {
  id: string;
  kickoff_at: string;
  status: string;
  venue?: string;
  matchday?: number;
  is_demo: boolean;
  home_score?: number | null;
  away_score?: number | null;
  home_xg?: number | null;
  away_xg?: number | null;
  competition: {
    id: string;
    name: string;
    country: string;
    code?: string;
    season: string;
  };
  home_team: { id: string; name: string; short_name?: string; elo_rating: number; country: string };
  away_team: { id: string; name: string; short_name?: string; elo_rating: number; country: string };
  prediction?: Prediction | null;
};

export type Market = {
  market: string;
  selection: string;
  probability: number;
  confidence: number;
  recommended: boolean;
  odds_decimal?: number | null;
  expected_value?: number | null;
  rationale?: string | null;
};

export type Prediction = {
  id: string;
  model_version: string;
  published_at: string;
  is_demo: boolean;
  home_win_prob: number;
  draw_prob: number;
  away_win_prob: number;
  confidence: number;
  expected_home_goals: number;
  expected_away_goals: number;
  most_likely_score: string;
  most_likely_score_prob: number;
  explanation_fr: string;
  explanation_en: string;
  key_factors: Record<string, unknown>;
  uncertainties: Record<string, unknown>;
  model_breakdown: Record<string, unknown>;
  markets: Market[];
};

export type Dashboard = {
  demo_mode: boolean;
  disclaimer_fr: string;
  disclaimer_en: string;
  today: Fixture[];
  tomorrow: Fixture[];
  next_7_days: Fixture[];
  finished: Fixture[];
  competitions: { id: string; name: string; country: string; code?: string; season: string }[];
};

function authHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("bp_access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  dashboard: (competitionId?: string) =>
    request<Dashboard>(`/fixtures/dashboard${competitionId ? `?competition_id=${competitionId}` : ""}`),
  fixture: (id: string) => request<Record<string, unknown>>(`/fixtures/${id}`),
  search: (q: string) => request<Fixture[]>(`/fixtures/search?q=${encodeURIComponent(q)}`),
  performance: () => request<Record<string, unknown>>("/predictions/performance"),
  history: () => request<Record<string, unknown>[]>("/predictions/history"),
  plans: () => request<{ plan: string; price_eur_monthly: number; features: string[] }[]>("/subscriptions/plans"),
  login: (email: string, password: string, mfa_code?: string) =>
    request<{ access_token: string; refresh_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, mfa_code }),
    }),
  register: (payload: {
    email: string;
    password: string;
    full_name: string;
    date_of_birth: string;
    locale?: string;
  }) =>
    request<{ access_token: string; refresh_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  me: () => request<Record<string, unknown>>("/auth/me"),
  budget: () => request<Record<string, unknown>>("/budget"),
  updateBudget: (payload: Record<string, unknown>) =>
    request("/budget", { method: "PUT", body: JSON.stringify(payload) }),
  addStake: (payload: Record<string, unknown>) =>
    request("/budget/decisions", { method: "POST", body: JSON.stringify(payload) }),
  checkout: (plan: string, provider = "stripe") =>
    request<Record<string, unknown>>("/subscriptions/checkout", {
      method: "POST",
      body: JSON.stringify({ plan, provider }),
    }),
  adminOverview: () => request<Record<string, unknown>>("/admin/overview"),
  adminSync: () => request<Record<string, unknown>>("/admin/sync", { method: "POST" }),
  adminUsers: () => request<Record<string, unknown>[]>("/admin/users"),
  notificationPrefs: () => request<Record<string, unknown>>("/notifications/preferences"),
  updateNotificationPrefs: (payload: Record<string, unknown>) =>
    request("/notifications/preferences", { method: "PUT", body: JSON.stringify(payload) }),
};

export function pct(v: number): string {
  return `${Math.round(v * 100)}%`;
}
