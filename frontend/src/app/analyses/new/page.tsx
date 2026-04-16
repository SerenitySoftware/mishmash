"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, type Analysis, type DatasetList } from "@/lib/api";
import { CodeEditor } from "@/components/CodeEditor";
import { useAuth } from "@/lib/auth";

const STARTER_CODE: Record<string, string> = {
  python: `import pandas as pd
import os

# Datasets are in the /data/ directory (or MISHMASH_DATA_DIR env var)
data_dir = os.environ.get("MISHMASH_DATA_DIR", "/data")
output_dir = os.environ.get("MISHMASH_OUTPUT_DIR", "/output")

# Example: df = pd.read_csv(f"{data_dir}/my-dataset.csv")
# Write results to output_dir for proof-of-work verification
# Example: df.to_csv(f"{output_dir}/results.csv", index=False)

print("Hello from Mishmash!")
`,
  r: `# Datasets are in /data/ (or MISHMASH_DATA_DIR env var)
data_dir <- Sys.getenv("MISHMASH_DATA_DIR", "/data")
output_dir <- Sys.getenv("MISHMASH_OUTPUT_DIR", "/output")

# Example: df <- read.csv(file.path(data_dir, "my-dataset.csv"))
# Write output to output_dir
# Example: write.csv(df, file.path(output_dir, "results.csv"), row.names=FALSE)

print("Hello from Mishmash!")
`,
  sql: `-- SQL analyses run against linked datasets
SELECT * FROM my_dataset LIMIT 10;
`,
};

export default function NewAnalysisPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("python");
  const [sourceCode, setSourceCode] = useState(STARTER_CODE.python);
  const [datasets, setDatasets] = useState<{ dataset_id: string; alias: string }[]>([]);
  const [availableDatasets, setAvailableDatasets] = useState<DatasetList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  useEffect(() => {
    apiFetch<DatasetList>("/api/datasets?page_size=100").then(setAvailableDatasets).catch(() => {});
  }, []);

  if (!user) return null;

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    if (sourceCode === STARTER_CODE[language]) setSourceCode(STARTER_CODE[lang]);
  };

  const addDataset = (datasetId: string) => {
    if (datasets.some((d) => d.dataset_id === datasetId)) return;
    const ds = availableDatasets?.items.find((d) => d.id === datasetId);
    setDatasets([...datasets, { dataset_id: datasetId, alias: ds?.slug || datasetId.slice(0, 8) }]);
  };

  const removeDataset = (idx: number) => {
    setDatasets(datasets.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const analysis = await apiFetch<Analysis>("/api/analyses", {
        method: "POST",
        body: JSON.stringify({
          title, description: description || null, language, source_code: sourceCode,
          datasets: datasets.map((d) => ({ dataset_id: d.dataset_id, alias: d.alias })),
        }),
      });
      router.push(`/analyses/${analysis.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create analysis");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">New Analysis</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" placeholder="My Analysis" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" placeholder="What does this analysis do?" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
            <select value={language} onChange={(e) => handleLanguageChange(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
              <option value="python">Python</option>
              <option value="r">R</option>
              <option value="sql">SQL</option>
            </select>
          </div>
        </div>

        {/* Dataset linking */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-3">
          <label className="block text-sm font-medium text-gray-700">Linked Datasets</label>
          {datasets.length > 0 && (
            <div className="space-y-2">
              {datasets.map((d, i) => {
                const ds = availableDatasets?.items.find((x) => x.id === d.dataset_id);
                return (
                  <div key={d.dataset_id} className="flex items-center gap-3 text-sm">
                    <span className="font-medium">{ds?.name || d.dataset_id.slice(0, 12)}</span>
                    <span className="text-gray-400">as</span>
                    <input type="text" value={d.alias}
                      onChange={(e) => { const copy = [...datasets]; copy[i].alias = e.target.value; setDatasets(copy); }}
                      className="rounded border border-gray-300 px-2 py-1 text-sm w-32" placeholder="alias" />
                    <button type="button" onClick={() => removeDataset(i)} className="text-red-500 hover:text-red-700 text-xs">Remove</button>
                  </div>
                );
              })}
            </div>
          )}
          {availableDatasets && availableDatasets.items.length > 0 && (
            <select onChange={(e) => { if (e.target.value) addDataset(e.target.value); e.target.value = ""; }}
              className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 outline-none">
              <option value="">+ Add a dataset...</option>
              {availableDatasets.items.filter((d) => !datasets.some((x) => x.dataset_id === d.id)).map((d) => (
                <option key={d.id} value={d.id}>{d.name} ({d.format})</option>
              ))}
            </select>
          )}
        </div>

        {/* Code editor */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Code</label>
          <CodeEditor value={sourceCode} onChange={setSourceCode} language={language} height="400px" />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <div className="flex gap-3">
          <button type="submit" disabled={submitting || !title.trim() || !sourceCode.trim()}
            className="rounded-lg bg-brand-600 px-6 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition">
            {submitting ? "Creating..." : "Create Analysis"}
          </button>
        </div>
      </form>
    </div>
  );
}
