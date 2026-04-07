"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, type Analysis, type AnalysisRun, type Comment } from "@/lib/api";
import { CodeEditor } from "@/components/CodeEditor";
import { CommentThread } from "@/components/CommentThread";
import { StarButton } from "@/components/StarButton";
import { useAuth } from "@/lib/auth";

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const { user } = useAuth();

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editCode, setEditCode] = useState("");

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
      setEditCode(a.source_code);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await apiFetch(`/api/analyses/${id}/run`, { method: "POST" });
      setTimeout(fetchData, 2000);
      setTimeout(fetchData, 5000);
      setTimeout(fetchData, 10000);
    } finally {
      setRunning(false);
    }
  };

  const handleFork = async () => {
    try {
      const forked = await apiFetch<Analysis>(`/api/analyses/${id}/fork`, {
        method: "POST",
        body: JSON.stringify({}),
      });
      router.push(`/analyses/${forked.id}`);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Fork failed");
    }
  };

  const handleSave = async () => {
    try {
      await apiFetch(`/api/analyses/${id}`, {
        method: "PUT",
        body: JSON.stringify({ source_code: editCode }),
      });
      setEditing(false);
      fetchData();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Save failed");
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (!analysis) return <div className="text-center py-12 text-gray-500">Analysis not found</div>;

  const isOwner = user && user.id === analysis.owner_id;
  const latestRun = runs[0];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{analysis.title}</h1>
            {analysis.forked_from_id && <span className="text-sm text-gray-400">forked</span>}
          </div>
          {analysis.owner && (
            <Link href={`/u/${analysis.owner.username}`} className="text-sm text-gray-500 hover:text-brand-600">
              @{analysis.owner.username}
            </Link>
          )}
          {analysis.description && <p className="mt-1 text-gray-600">{analysis.description}</p>}
          <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
            <span className="rounded bg-gray-100 px-2 py-0.5 uppercase text-xs font-medium">{analysis.language}</span>
            <span>{analysis.datasets.length} dataset(s)</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StarButton targetType="analysis" targetId={analysis.id} initialStarCount={analysis.star_count} />
          {user && (
            <button onClick={handleFork} className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium hover:bg-gray-50 transition">
              Fork ({analysis.fork_count})
            </button>
          )}
          {user && (
            <button onClick={handleRun} disabled={running} className="rounded-lg bg-green-600 px-4 py-1.5 text-sm text-white font-medium hover:bg-green-700 disabled:opacity-50 transition">
              {running ? "Starting..." : "Run"}
            </button>
          )}
        </div>
      </div>

      {/* Code */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">Source Code</h2>
          {isOwner && (
            editing ? (
              <div className="flex gap-2">
                <button onClick={handleSave} className="rounded-lg bg-brand-600 px-3 py-1 text-sm text-white hover:bg-brand-700 transition">Save</button>
                <button onClick={() => { setEditing(false); setEditCode(analysis.source_code); }} className="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 transition">Cancel</button>
              </div>
            ) : (
              <button onClick={() => setEditing(true)} className="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 transition">Edit</button>
            )
          )}
        </div>
        <CodeEditor
          value={editing ? editCode : analysis.source_code}
          onChange={setEditCode}
          language={analysis.language}
          height="300px"
          readOnly={!editing}
        />
      </div>

      {/* PoW info box */}
      <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 text-sm text-blue-800">
        <strong>Run locally with proof-of-work:</strong> Install the Mishmash CLI and run{" "}
        <code className="bg-blue-100 rounded px-1">mishmash run {analysis.id}</code>{" "}
        to execute this analysis on your machine with cryptographic verification.
      </div>

      {/* Latest run */}
      {latestRun && (
        <div className="space-y-3">
          <h2 className="text-lg font-semibold">Latest Run</h2>
          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex items-center gap-3 text-sm">
              <RunStatusBadge status={latestRun.status} />
              {latestRun.duration_ms && <span className="text-gray-500">{(latestRun.duration_ms / 1000).toFixed(1)}s</span>}
              <span className="text-gray-500">{new Date(latestRun.created_at).toLocaleString()}</span>
              {latestRun.pow_verified && (
                <span className="rounded bg-green-100 px-2 py-0.5 text-green-700 text-xs font-medium">
                  PoW Verified
                </span>
              )}
              {latestRun.environment_hash && (
                <span className="text-xs text-gray-400">env: {latestRun.environment_hash.slice(0, 12)}...</span>
              )}
            </div>
            {latestRun.stdout && (
              <div className="mt-3">
                <h4 className="text-xs font-medium text-gray-500 mb-1">Output</h4>
                <pre className="rounded bg-gray-900 text-gray-100 p-3 text-sm overflow-x-auto max-h-64 overflow-y-auto">{latestRun.stdout}</pre>
              </div>
            )}
            {latestRun.stderr && (
              <div className="mt-3">
                <h4 className="text-xs font-medium text-red-500 mb-1">Errors</h4>
                <pre className="rounded bg-red-50 text-red-800 p-3 text-sm overflow-x-auto max-h-64 overflow-y-auto">{latestRun.stderr}</pre>
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
                <RunStatusBadge status={run.status} />
                {run.duration_ms && <span className="text-gray-500">{(run.duration_ms / 1000).toFixed(1)}s</span>}
                <span className="text-gray-500">{new Date(run.created_at).toLocaleString()}</span>
                {run.pow_verified && <span className="rounded bg-green-100 px-2 py-0.5 text-green-700 text-xs">PoW</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Comments */}
      <CommentThread targetType="analysis" targetId={analysis.id} comments={comments} onRefresh={fetchData} />
    </div>
  );
}

function RunStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    running: "bg-yellow-100 text-yellow-700",
    queued: "bg-gray-100 text-gray-700",
  };
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-medium ${colors[status] || colors.queued}`}>
      {status}
    </span>
  );
}
