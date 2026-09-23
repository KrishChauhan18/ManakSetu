/**
 * Centralized API service for ComplyErg / Manak Setu.
 * All calls go through /api/v1 (proxied by Vite dev server to http://127.0.0.1:8000).
 * Backend wraps every response in { success: bool, data: T, error: ... }.
 */

const BASE_URL = "/api/v1";

const TOKEN_KEY = "metriaegis_token";

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Unwrap the backend envelope. Throws on error. */
async function unwrap<T>(res: Response): Promise<T> {
  const json = await res.json().catch(() => null);
  if (!res.ok) {
    const msg =
      json?.error?.message ||
      json?.detail ||
      `Request failed with status ${res.status}`;
    throw new Error(msg);
  }
  if (json && "data" in json) return json.data as T;
  return json as T;
}

// ─── Auth ──────────────────────────────────────────────────────────────────

export interface LoginResponse {
  token: string;
  access_token: string;
  token_type: string;
  role: string;
  user_id: number;
  email: string;
}

export async function apiLogin(
  email: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return unwrap<LoginResponse>(res);
}

export interface MeResponse {
  id: number;
  email: string;
  role: string;
  region: string | null;
  is_active: boolean;
}

export async function apiGetMe(): Promise<MeResponse> {
  const res = await fetch(`${BASE_URL}/auth/me`, {
    headers: authHeaders(),
  });
  return unwrap<MeResponse>(res);
}

// ─── Dashboard ─────────────────────────────────────────────────────────────

export interface DashboardStats {
  total_scans: number;
  overall_compliance_pct: number;
  severity_breakdown: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    manual_review: number;
  };
}

export async function apiGetDashboardStats(
  category?: string
): Promise<DashboardStats> {
  const params = category && category !== "all" ? `?category=${category}` : "";
  const res = await fetch(`${BASE_URL}/dashboard/stats${params}`, {
    headers: authHeaders(),
  });
  return unwrap<DashboardStats>(res);
}

export interface TrendPoint {
  date: string;
  avg_compliance_pct: number;
  scan_count: number;
}

export async function apiGetTrend(
  days = 30,
  category?: string
): Promise<{ days: number; trend: TrendPoint[] }> {
  const params = new URLSearchParams({ days: String(days) });
  if (category && category !== "all") params.set("category", category);
  const res = await fetch(`${BASE_URL}/dashboard/trend?${params}`, {
    headers: authHeaders(),
  });
  return unwrap(res);
}

export interface TopViolation {
  rule_id: string;
  field: string;
  severity: string;
  count: number;
}

export async function apiGetTopViolations(
  limit = 5,
  category?: string
): Promise<TopViolation[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (category && category !== "all") params.set("category", category);
  const res = await fetch(`${BASE_URL}/dashboard/top-violations?${params}`, {
    headers: authHeaders(),
  });
  return unwrap(res);
}

export interface ManufacturerRank {
  manufacturer_name: string;
  total_scans: number;
  avg_compliance_pct: number;
}

export async function apiGetManufacturerRanking(
  category?: string
): Promise<ManufacturerRank[]> {
  const params =
    category && category !== "all" ? `?category=${category}` : "";
  const res = await fetch(
    `${BASE_URL}/dashboard/manufacturer-ranking${params}`,
    { headers: authHeaders() }
  );
  return unwrap(res);
}

// ─── Scans ─────────────────────────────────────────────────────────────────

export interface Violation {
  id: number;
  rule_id: string;
  legal_rule_ref: string;
  source_law: string;
  field: string;
  severity: string;
  status: string;
  detected_value: string | null;
  expected: string | null;
  confidence: number;
  bbox: unknown;
  message: string;
  recommendation: string | null;
}

export interface ScanRecord {
  id: number;
  user_id: number | null;
  image_path: string;
  image_url: string;
  annotated_image_url: string;
  pdf_report_url: string;
  category: string;
  status: string;
  compliance_pct: number;
  label_record: Record<string, unknown> | null;
  created_at: string | null;
  gps_lat: number | null;
  gps_lng: number | null;
  violations: Violation[];
}

export interface ScanListResponse {
  items: ScanRecord[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export async function apiListScans(params?: {
  category?: string;
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<ScanListResponse> {
  const q = new URLSearchParams();
  if (params?.category && params.category !== "all")
    q.set("category", params.category);
  if (params?.status && params.status !== "all")
    q.set("status", params.status);
  if (params?.search) q.set("search", params.search);
  if (params?.page) q.set("page", String(params.page));
  if (params?.page_size) q.set("page_size", String(params.page_size));

  const res = await fetch(`${BASE_URL}/scan/?${q}`, {
    headers: authHeaders(),
  });
  return unwrap(res);
}

export async function apiGetScan(scanId: number | string): Promise<ScanRecord> {
  const res = await fetch(`${BASE_URL}/scan/${scanId}`, {
    headers: authHeaders(),
  });
  return unwrap(res);
}

export async function apiUploadScan(
  file: File,
  category: string,
  gps_lat?: number,
  gps_lng?: number
): Promise<ScanRecord> {
  const form = new FormData();
  form.append("file", file);
  form.append("category", category);
  if (gps_lat !== undefined) form.append("gps_lat", String(gps_lat));
  if (gps_lng !== undefined) form.append("gps_lng", String(gps_lng));

  const res = await fetch(`${BASE_URL}/scan/upload`, {
    method: "POST",
    headers: authHeaders(),
    body: form,
  });
  return unwrap(res);
}

export async function apiDeleteScan(scanId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/scan/${scanId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  await unwrap(res);
}

// ─── Reports ───────────────────────────────────────────────────────────────

/** Returns the URL to download the PDF directly (opens in new tab). */
export function getPdfUrl(scanId: number | string): string {
  return `${BASE_URL}/reports/${scanId}/pdf`;
}

export function getCsvUrl(scanId: number | string): string {
  return `${BASE_URL}/reports/${scanId}/csv`;
}

export function getJsonUrl(scanId: number | string): string {
  return `${BASE_URL}/reports/${scanId}/json`;
}

// ─── Rules ─────────────────────────────────────────────────────────────────

export interface RuleRecord {
  id: number;
  rule_id_str: string;
  legal_rule_ref: string;
  source_law: string;
  field: string;
  check_type: string;
  pattern: string | null;
  severity: string;
  category: string[] | string;
  version: string;
  enabled: boolean;
}

export interface RuleListResponse {
  items: RuleRecord[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export async function apiListRules(params?: {
  category?: string;
  enabled?: boolean;
  page?: number;
  page_size?: number;
}): Promise<RuleListResponse | RuleRecord[]> {
  const q = new URLSearchParams();
  if (params?.category && params.category !== "all")
    q.set("category", params.category);
  if (params?.enabled !== undefined) q.set("enabled", String(params.enabled));
  if (params?.page) q.set("page", String(params.page));
  if (params?.page_size) q.set("page_size", String(params.page_size));

  const res = await fetch(`${BASE_URL}/rules/?${q}`, {
    headers: authHeaders(),
  });
  return unwrap(res);
}

export async function apiToggleRule(
  ruleIdStr: string,
  enabled: boolean
): Promise<RuleRecord> {
  const res = await fetch(`${BASE_URL}/rules/${ruleIdStr}`, {
    method: "PUT",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  return unwrap(res);
}

export async function apiCreateRule(
  rule: Omit<RuleRecord, "id">
): Promise<RuleRecord> {
  const res = await fetch(`${BASE_URL}/rules/`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(rule),
  });
  return unwrap(res);
}

export async function apiDeleteRule(ruleIdStr: string): Promise<void> {
  const res = await fetch(`${BASE_URL}/rules/${ruleIdStr}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  await unwrap(res);
}

// ─── Users ─────────────────────────────────────────────────────────────────

export interface UserRecord {
  id: number;
  email: string;
  role: string;
  region: string | null;
  supervisor_id: number | null;
  is_active: boolean;
  created_at: string | null;
}

export interface UserListResponse {
  items: UserRecord[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export async function apiListUsers(params?: {
  role?: string;
  region?: string;
  page?: number;
  page_size?: number;
}): Promise<UserListResponse | UserRecord[]> {
  const q = new URLSearchParams();
  if (params?.role) q.set("role", params.role);
  if (params?.region) q.set("region", params.region);
  if (params?.page) q.set("page", String(params.page));
  if (params?.page_size) q.set("page_size", String(params.page_size));

  const res = await fetch(`${BASE_URL}/users/?${q}`, {
    headers: authHeaders(),
  });
  return unwrap(res);
}

export async function apiCreateUser(payload: {
  email: string;
  password: string;
  role: string;
  region?: string;
  supervisor_id?: number;
}): Promise<UserRecord> {
  const res = await fetch(`${BASE_URL}/users/`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return unwrap(res);
}

export async function apiUpdateUser(
  userId: number,
  payload: {
    role?: string;
    region?: string;
    is_active?: boolean;
    supervisor_id?: number;
  }
): Promise<UserRecord> {
  const res = await fetch(`${BASE_URL}/users/${userId}`, {
    method: "PUT",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return unwrap(res);
}

export async function apiDeleteUser(userId: number): Promise<void> {
  const res = await fetch(`${BASE_URL}/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  await unwrap(res);
}

// ─── Audit Log ─────────────────────────────────────────────────────────────

export interface AuditLogEntry {
  id: number;
  user_id: number | null;
  action: string;
  target_type: string;
  target_id: string;
  old_value: unknown;
  new_value: unknown;
  reason: string | null;
  timestamp: string | null;
}

export interface AuditListResponse {
  items: AuditLogEntry[];
  pagination: {
    page: number;
    page_size: number;
    total: number;
    total_pages: number;
  };
}

export async function apiGetAuditLogs(params?: {
  target_type?: string;
  action?: string;
  user_id?: number;
  page?: number;
  page_size?: number;
}): Promise<AuditListResponse> {
  const q = new URLSearchParams();
  if (params?.target_type) q.set("target_type", params.target_type);
  if (params?.action) q.set("action", params.action);
  if (params?.user_id) q.set("user_id", String(params.user_id));
  if (params?.page) q.set("page", String(params.page));
  if (params?.page_size) q.set("page_size", String(params.page_size));

  const res = await fetch(`${BASE_URL}/audit/?${q}`, {
    headers: authHeaders(),
  });
  return unwrap(res);
}

// ─── Scan image ────────────────────────────────────────────────────────────

export function getScanImageUrl(
  scanId: number | string,
  annotated = false
): string {
  return `${BASE_URL}/scan/${scanId}/image${annotated ? "?annotated=true" : ""}`;
}
