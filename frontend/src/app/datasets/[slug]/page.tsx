"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { apiFetch, type Dataset, type DatasetPreview, type Comment } from "@/lib/api";
import { DataTable } from "@/components/DataTable";
import { CommentThread } from "@/components/CommentThread";

export default function DatasetDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"preview" | "schema" | "comments">("preview");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const ds = await apiFetch<Dataset>(`/api/datasets/${slug}`);
      setDataset(ds);

      try {
        const prev = await apiFetch<DatasetPreview>(
          `/api/datasets/${ds.id}/preview?limit=50`
        );
        setPreview(prev);
      } catch {
        // Preview might fail if no versions uploaded yet
      }

      const cmts = await apiFetch<Comment[]>(
        `/api/comments?target_type=dataset&target_id=${ds.id}`
      );
      setComments(cmts);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return <div className="text-center py-12 text-gray-500">Loading...</div>;
  }

  if (!dataset) {
    return <div className="text-center py-12 text-gray-500">Dataset not found</div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">{dataset.name}</h1>
        {dataset.description && (
          <p className="mt-2 text-gray-600">{dataset.description}</p>
        )}
        <div className="mt-3 flex items-center gap-4 text-sm text-gray-500">
          <span className="rounded bg-gray-100 px-2 py-0.5 uppercase font-medium text-xs">
            {dataset.format}
          </span>
          {dataset.row_count !== null && (
            <span>{dataset.row_count.toLocaleString()} rows</span>
          )}
          <span>v{dataset.current_version}</span>
          {dataset.tags.map((tag) => (
            <span
              key={tag}
              className="rounded bg-brand-50 px-2 py-0.5 text-brand-700 text-xs"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-4">
          {(["preview", "schema", "comments"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 text-sm font-medium capitalize transition ${
                activeTab === tab
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab}
              {tab === "comments" && ` (${comments.length})`}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      {activeTab === "preview" && preview && (
        <DataTable
          columns={preview.columns}
          rows={preview.rows}
          dtypes={preview.dtypes}
        />
      )}

      {activeTab === "preview" && !preview && (
        <div className="text-center py-8 text-gray-500">
          No data uploaded yet. Upload a file to see a preview.
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
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Range</th>
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
                    {col.min !== undefined ? `${col.min} - ${col.max}` : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === "comments" && (
        <CommentThread
          targetType="dataset"
          targetId={dataset.id}
          comments={comments}
          onRefresh={fetchData}
        />
      )}
    </div>
  );
}
