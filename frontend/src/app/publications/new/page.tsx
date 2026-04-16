"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, type Publication, type DatasetList, type AnalysisList } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function NewPublicationPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [refs, setRefs] = useState<{ ref_type: string; ref_id: string }[]>([]);
  const [datasets, setDatasets] = useState<DatasetList | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  useEffect(() => {
    apiFetch<DatasetList>("/api/datasets?page_size=50").then(setDatasets).catch(() => {});
    apiFetch<AnalysisList>("/api/analyses?page_size=50").then(setAnalyses).catch(() => {});
  }, []);

  if (!user) return null;

  const addRef = (type: string, id: string) => {
    if (refs.some((r) => r.ref_type === type && r.ref_id === id)) return;
    setRefs([...refs, { ref_type: type, ref_id: id }]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const pub = await apiFetch<Publication>("/api/publications", {
        method: "POST",
        body: JSON.stringify({ title, body, references: refs }),
      });
      router.push(`/publications/${pub.slug}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create publication");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">New Publication</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" placeholder="My Research Findings" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Body (Markdown)</label>
            <textarea value={body} onChange={(e) => setBody(e.target.value)} required rows={20}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
              placeholder={`## Summary\n\nDescribe your findings...\n\n## Methodology\n\n## Results\n\n## Conclusion`} />
          </div>
        </div>

        {/* References */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-3">
          <label className="block text-sm font-medium text-gray-700">Linked References</label>
          {refs.length > 0 && (
            <div className="space-y-2">
              {refs.map((r, i) => (
                <div key={`${r.ref_type}-${r.ref_id}`} className="flex items-center gap-2 text-sm">
                  <span className="rounded bg-blue-50 px-2 py-0.5 text-blue-700 text-xs font-medium">{r.ref_type}</span>
                  <span className="text-gray-600">{r.ref_id.slice(0, 12)}...</span>
                  <button type="button" onClick={() => setRefs(refs.filter((_, j) => j !== i))} className="text-red-500 text-xs">Remove</button>
                </div>
              ))}
            </div>
          )}
          <div className="flex gap-2">
            {datasets && datasets.items.length > 0 && (
              <select onChange={(e) => { if (e.target.value) addRef("dataset", e.target.value); e.target.value = ""; }}
                className="rounded-lg border border-gray-300 px-2 py-1 text-sm">
                <option value="">+ Link dataset...</option>
                {datasets.items.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            )}
            {analyses && analyses.items.length > 0 && (
              <select onChange={(e) => { if (e.target.value) addRef("analysis_run", e.target.value); e.target.value = ""; }}
                className="rounded-lg border border-gray-300 px-2 py-1 text-sm">
                <option value="">+ Link analysis...</option>
                {analyses.items.map((a) => <option key={a.id} value={a.id}>{a.title}</option>)}
              </select>
            )}
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={submitting || !title.trim() || !body.trim()}
          className="rounded-lg bg-brand-600 px-6 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition">
          {submitting ? "Publishing..." : "Publish"}
        </button>
      </form>
    </div>
  );
}
