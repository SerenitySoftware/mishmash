const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("mishmash_token");
}

export function setToken(token: string) {
  localStorage.setItem("mishmash_token", token);
}

export function clearToken() {
  localStorage.removeItem("mishmash_token");
  localStorage.removeItem("mishmash_user");
}

export function getStoredUser(): UserOut | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("mishmash_user");
  return raw ? JSON.parse(raw) : null;
}

export function setStoredUser(user: UserOut) {
  localStorage.setItem("mishmash_user", JSON.stringify(user));
}

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string> || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    clearToken();
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// User types
export interface UserOut {
  id: string;
  email: string;
  username: string;
  name: string;
  bio: string | null;
  avatar_url: string | null;
  created_at: string;
}

export interface UserProfile {
  id: string;
  username: string;
  name: string;
  bio: string | null;
  avatar_url: string | null;
  created_at: string;
  dataset_count: number;
  analysis_count: number;
  publication_count: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

// Dataset types
export interface Owner {
  id: string;
  username: string;
  name: string;
  avatar_url: string | null;
}

export interface Dataset {
  id: string;
  owner_id: string;
  owner: Owner | null;
  name: string;
  slug: string;
  description: string | null;
  tags: string[];
  format: string;
  current_version: number;
  row_count: number | null;
  column_meta: ColumnMeta[] | null;
  license: string | null;
  is_public: boolean;
  star_count: number;
  fork_count: number;
  download_count: number;
  forked_from_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ColumnMeta {
  name: string;
  dtype: string;
  nullable: boolean;
  unique_count?: number;
  min?: number;
  max?: number;
  mean?: number;
}

export interface DatasetList {
  items: Dataset[];
  total: number;
  page: number;
  page_size: number;
}

export interface DatasetVersion {
  id: string;
  version: number;
  file_size_bytes: number | null;
  row_count: number | null;
  column_meta: ColumnMeta[] | null;
  created_at: string;
}

export interface DatasetPreview {
  columns: string[];
  dtypes: Record<string, string>;
  rows: Record<string, unknown>[];
  total_rows: number | null;
}

export interface DatasetReference {
  id: string;
  source_id: string;
  target_id: string;
  relationship_type: string;
  description: string | null;
  created_at: string;
}

// Analysis types
export interface Analysis {
  id: string;
  owner_id: string;
  owner: Owner | null;
  title: string;
  description: string | null;
  language: string;
  source_code: string;
  status: string;
  star_count: number;
  fork_count: number;
  forked_from_id: string | null;
  datasets: AnalysisDataset[];
  created_at: string;
  updated_at: string;
}

export interface AnalysisDataset {
  dataset_id: string;
  version: number | null;
  alias: string | null;
}

export interface AnalysisList {
  items: Analysis[];
  total: number;
  page: number;
  page_size: number;
}

export interface AnalysisRun {
  id: string;
  analysis_id: string;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  stdout: string | null;
  stderr: string | null;
  result_key: string | null;
  result_meta: Record<string, unknown> | null;
  error_message: string | null;
  pow_hash: string | null;
  pow_nonce: string | null;
  pow_verified: boolean | null;
  environment_hash: string | null;
  created_at: string;
}

// Comment types
export interface Author {
  id: string;
  username: string;
  name: string;
  avatar_url: string | null;
}

export interface Comment {
  id: string;
  author_id: string;
  author: Author | null;
  target_type: string;
  target_id: string;
  parent_id: string | null;
  body: string;
  created_at: string;
  updated_at: string;
  replies: Comment[];
}

// Publication types
export interface Publication {
  id: string;
  author_id: string;
  author: Author | null;
  title: string;
  slug: string;
  body: string;
  references: PublicationReference[];
  created_at: string;
  updated_at: string;
}

export interface PublicationReference {
  ref_type: string;
  ref_id: string;
}

export interface PublicationList {
  items: Publication[];
  total: number;
  page: number;
  page_size: number;
}
