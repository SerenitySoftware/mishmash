"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, type Dataset, type DatasetPreview, type DatasetVersion, type DatasetReference, type Comment } from "@/lib/api";
import { DataTable } from "@/components/DataTable";
import { CommentThread } from "@/components/CommentThread";
import { StarButton } from "@/components/StarButton";
import { FileUploader } from "@/components/FileUploader";
import { useAuth } from "@/lib/auth";

export default function DatasetDetailPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { user } = useAuth();

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [versions, setVersions] = useState<DatasetVersion[]>([]);
  const [references, setReferences] = useState<DatasetReference[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"preview" | "schema" | "versions" | "references" | "comments">("preview");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const ds = await apiFetch<Dataset>(`/api/datasets/${slug}`);
      setDataset(ds);

      const [cmts, vers, refs] = await Promise.all([
        apiFetch<Comment[]>(`/api/comments?target_type=dataset&target_id=${ds.id}`),
        apiFetch<DatasetVersion[]>(`/api/datasets/${ds.id}/versions`),
        apiFetch<DatasetReference[]>(`/api/datasets/${ds.id}/references`),
      ]);
      setComments(cmts);
      setVersions(vers);
      setReferences(refs);

      try {
        const prev = await apiFetch<DatasetPreview>(`/api/datasets/${ds.id}/preview?limit=50`);
        setPreview(prev);
      } catch {}
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleFork = async () => {
    if (!dataset) return;
    try {
      const forked = await apiFetch<Dataset>(`/api/datasets/${dataset.id}/fork`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      router.push(`/datasets/${forked.slug}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Fork failed");
    }
  };

  const handleDownload = async () => {
    if (!dataset) return;
    const resp = await apiFetch<{ download_url: string }>(`/api/datasets/${dataset.id}/download`);
    window.open(resp.download_url, "_blank");
  };

  const handleUploadVersion = async (file: File) => {
    if (!dataset) return;
    const { upload_url, storage_key } = await apiFetch<{ upload_url: string; storage_key: string }>(
      `/api/datasets/${dataset.id}/upload?filename=${encodeURIComponent(file.name)}`,
      { method: "POST" }
    );
    await fetch(upload_url, { method: "PUT", body: file, headers: { "Content-Type": "application/octet-stream" } });
    await apiFetch(`/api/datasets/${dataset.id}/upload/complete`, {
      method: "POST",
      body: JSON.stringify({ dataset_id: dataset.id, storage_key, file_size_bytes: file.size }),
    });
    fetchData();
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (!dataset) return <div className="text-center py-12 text-gray-500">Dataset not found</div>;

  const isOwner = user && user.id === dataset.owner_id;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{dataset.name}</h1>
            {dataset.forked_from_id && (
              <span className="text-sm text-gray-400">forked</span>
            )}
          </div>
          {dataset.owner && (
            <Link href={`/u/${dataset.owner.username}`} className="text-sm text-gray-500 hover:text-brand-600">
              @{dataset.owner.username}
            </Link>
          )}
          {dataset.description && <p className="mt-2 text-gray-600">{dataset.description}</p>}
          <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
            <span className="rounded bg-gray-100 px-2 py-0.5 uppercase font-medium text-xs">{dataset.format}</span>
            {dataset.row_count !== null && <span>{dataset.row_count.toLocaleString()} rows</span>}
            <span>v{dataset.current_version}</span>
            <span>{dataset.download_count} downloads</span>
            {dataset.license && <span>{dataset.license}</span>}
            {dataset.tags.map((tag) => (
              <span key={tag} className="rounded bg-brand-50 px-2 py-0.5 text-brand-700 text-xs">{tag}</span>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StarButton targetType="dataset" targetId={dataset.id} initialStarCount={dataset.star_count} />
          {user && (
            <button onClick={handleFork} className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 transition">
              Fork ({dataset.fork_count})
            </button>
          )}
          <button onClick={handleDownload} className="rounded-lg bg-brand-600 px-4 py-1.5 text-sm text-white font-medium hover:bg-brand-700 transition">
            Download
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-4">
          {(["preview", "schema", "versions", "references", "comments"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 text-sm font-medium capitalize transition ${
                activeTab === tab ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab}{tab === "comments" ? ` (${comments.length})` : tab === "references" ? ` (${references.length})` : tab === "versions" ? ` (${versions.length})` : ""}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "preview" && preview && (
        <DataTable columns={preview.columns} rows={preview.rows} dtypes={preview.dtypes} />
      )}
      {activeTab === "preview" && !preview && (
        <div className="text-center py-8 text-gray-500">
          {isOwner ? (
            <div className="space-y-4">
              <p>No data uploaded yet. Upload a file to get started.</p>
              <FileUploader onUpload={handleUploadVersion} />
            </div>
          ) : "No data available yet."}
        </div>
      )}

      {activeTab === "schema" && dataset.column_meta && (
        <div className="rounded-lg border border-gray-200 bg-white overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Column</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Nullable</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Unique</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Range / Mean</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {(dataset.column_meta as any[]).map((col: any) => (
                <tr key={col.name}>
                  <td className="px-4 py-2 text-sm font-medium">{col.name}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{col.dtype}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{col.nullable ? "Yes" : "No"}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">{col.unique_count ?? "-"}</td>
                  <td className="px-4 py-2 text-sm text-gray-600">
                    {col.min !== undefined ? `${col.min} - ${col.max} (avg ${col.mean?.toFixed(2)})` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "versions" && (
        <div className="space-y-4">
          {isOwner && (
            <div>
              <h3 className="text-sm font-medium mb-2">Upload new version</h3>
              <FileUploader onUpload={handleUploadVersion} />
            </div>
          )}
          <div className="rounded-lg border border-gray-200 bg-white divide-y">
            {versions.map((v) => (
              <div key={v.id} className="px-4 py-3 flex items-center justify-between text-sm">
                <div className="flex items-center gap-4">
                  <span className="font-medium">v{v.version}</span>
                  {v.row_count && <span className="text-gray-500">{v.row_count.toLocaleString()} rows</span>}
                  {v.file_size_bytes && <span className="text-gray-500">{(v.file_size_bytes / 1024 / 1024).toFixed(1)} MB</span>}
                </div>
                <span className="text-gray-400">{new Date(v.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === "references" && (
        <div className="space-y-4">
          {references.length === 0 ? (
            <p className="text-center py-8 text-gray-500">No references yet</p>
          ) : (
            <div className="rounded-lg border border-gray-200 bg-white divide-y">
              {references.map((ref) => (
                <div key={ref.id} className="px-4 py-3 flex items-center gap-4 text-sm">
                  <span className="rounded bg-blue-50 px-2 py-0.5 text-blue-700 text-xs font-medium">
                    {ref.relationship_type}
                  </span>
                  <span className="text-gray-600">
                    {ref.source_id === dataset.id ? `This -> ${ref.target_id.slice(0, 8)}...` : `${ref.source_id.slice(0, 8)}... -> This`}
                  </span>
                  {ref.description && <span className="text-gray-400">{ref.description}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "comments" && (
        <CommentThread targetType="dataset" targetId={dataset.id} comments={comments} onRefresh={fetchData} />
      )}
    </div>
  );
}
