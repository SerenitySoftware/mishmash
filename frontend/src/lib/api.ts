const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export async function apiFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// Dataset types
export interface Dataset {
  id: string;
  owner_id: string;
  name: string;
  slug: string;
  description: string | null;
  tags: string[];
  format: string;
  current_version: number;
  row_count: number | null;
  column_meta: ColumnMeta[] | null;
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

// Analysis types
export interface Analysis {
  id: string;
  owner_id: string;
  title: string;
  description: string | null;
  language: string;
  source_code: string;
  status: string;
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
  created_at: string;
}

// Comment types
export interface Comment {
  id: string;
  author_id: string;
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
