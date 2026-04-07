"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { apiFetch, type Analysis, type AnalysisRun, type Comment } from "@/lib/api";
import { CodeEditor } from "@/components/CodeEditor";
import { CommentThread } from "@/components/CommentThread";

export default function AnalysisDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [a, r, c] = await Promise.all([
        apiFetch<Analysis>(`/api/analyses/${id}`),
        apiFetch<AnalysisRun[]>(`/api/analyses/${id}/runs`),
        apiFetch<Comment[]>(`/api/comments?target_type=analysis&target_id=${id}`),
      ]);
      setAnalysis(a);
      setRuns(r);
      setComments(c);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await apiFetch(`/api/analyses/${id}/run`, { method: "POST" });
      // Poll for updates
      setTimeout(fetchData, 2000);
      setTimeout(fetchData, 5000);
      setTimeout(fetchData, 10000);
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (!analysis) return <div className="text-center py-12 text-gray-500">Analysis not found</div>;

  const latestRun = runs[0];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{analysis.title}</h1>
          {analysis.description && (
            <p className="mt-1 text-gray-600">{analysis.description}</p>
          )}
          <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
            <span className="rounded bg-gray-100 px-2 py-0.5 uppercase text-xs font-medium">
              {analysis.language}
            </span>
            <span>{analysis.datasets.length} dataset(s)</span>
          </div>
        </div>
        <button
          onClick={handleRun}
          disabled={running}
          className="rounded-lg bg-green-600 px-4 py-2 text-sm text-white font-medium hover:bg-green-700 disabled:opacity-50 transition"
        >
          {running ? "Starting..." : "Run Analysis"}
        </button>
      </div>

      {/* Code */}
      <div>
        <h2 className="text-lg font-semibold mb-2">Source Code</h2>
        <CodeEditor
          value={analysis.source_code}
          onChange={() => {}}
          language={analysis.language}
          height="300px"
          readOnly
        />
      </div>

      {/* Latest run */}
      {latestRun && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Latest Run</h2>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center gap-3 text-sm">
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${
                  latestRun.status === "completed"
                    ? "bg-green-100 text-green-700"
                    : latestRun.status === "failed"
                    ? "bg-red-100 text-red-700"
                    : latestRun.status === "running"
                    ? "bg-yellow-100 text-yellow-700"
                    : "bg-gray-100 text-gray-700"
                }`}
              >
                {latestRun.status}
              </span>
              {latestRun.duration_ms && (
                <span className="text-gray-500">
                  {(latestRun.duration_ms / 1000).toFixed(1)}s
                </span>
              )}
              <span className="text-gray-500">
                {new Date(latestRun.created_at).toLocaleString()}
              </span>
            </div>
            {latestRun.stdout && (
              <div className="mt-3">
                <h4 className="text-xs font-medium text-gray-500 mb-1">Output</h4>
                <pre className="rounded bg-gray-900 text-gray-100 p-3 text-sm overflow-x-auto max-h-64 overflow-y-auto">
                  {latestRun.stdout}
                </pre>
              </div>
            )}
            {latestRun.stderr && (
              <div className="mt-3">
                <h4 className="text-xs font-medium text-red-500 mb-1">Errors</h4>
                <pre className="rounded bg-red-50 text-red-800 p-3 text-sm overflow-x-auto max-h-64 overflow-y-auto">
                  {latestRun.stderr}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Run history */}
      {runs.length > 1 && (
        <div>
          <h2 className="text-lg font-semibold mb-2">Run History</h2>
          <div className="rounded-lg border border-gray-200 bg-white divide-y divide-gray-200">
            {runs.slice(1).map((run) => (
              <div key={run.id} className="px-4 py-3 flex items-center gap-3 text-sm">
                <span
                  className={`rounded px-2 py-0.5 text-xs font-medium ${
                    run.status === "completed"
                      ? "bg-green-100 text-green-700"
                      : run.status === "failed"
                      ? "bg-red-100 text-red-700"
                      : "bg-gray-100 text-gray-700"
                  }`}
                >
                  {run.status}
                </span>
                {run.duration_ms && (
                  <span className="text-gray-500">
                    {(run.duration_ms / 1000).toFixed(1)}s
                  </span>
                )}
                <span className="text-gray-500">
                  {new Date(run.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comments */}
      <CommentThread
        targetType="analysis"
        targetId={analysis.id}
        comments={comments}
        onRefresh={fetchData}
      />
    </div>
  );
}
