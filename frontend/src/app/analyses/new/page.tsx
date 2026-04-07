"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, type Analysis } from "@/lib/api";
import { CodeEditor } from "@/components/CodeEditor";

const STARTER_CODE: Record<string, string> = {
  python: `import pandas as pd

# Datasets are available in /data/ as {alias}.{format}
# Example: df = pd.read_csv("/data/my-dataset.csv")

# Write output files to /output/
# Example: df.to_csv("/output/results.csv", index=False)

print("Hello from Mishmash!")
`,
  r: `# Datasets are available in /data/ as {alias}.{format}
# Example: df <- read.csv("/data/my-dataset.csv")

# Write output files to /output/
# Example: write.csv(df, "/output/results.csv", row.names=FALSE)

print("Hello from Mishmash!")
`,
  sql: `-- SQL analyses run against linked datasets
-- Each dataset is available as a table named by its alias

SELECT * FROM my_dataset LIMIT 10;
`,
};

export default function NewAnalysisPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [language, setLanguage] = useState("python");
  const [sourceCode, setSourceCode] = useState(STARTER_CODE.python);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    if (sourceCode === STARTER_CODE[language]) {
      setSourceCode(STARTER_CODE[lang]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const analysis = await apiFetch<Analysis>("/api/analyses", {
        method: "POST",
        body: JSON.stringify({
          title,
          description: description || null,
          language,
          source_code: sourceCode,
          datasets: [],
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
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Title
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
            placeholder="My Analysis"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
            placeholder="What does this analysis do?"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            value={language}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
          >
            <option value="python">Python</option>
            <option value="r">R</option>
            <option value="sql">SQL</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Code
          </label>
          <CodeEditor
            value={sourceCode}
            onChange={setSourceCode}
            language={language}
            height="400px"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !title.trim() || !sourceCode.trim()}
          className="rounded-lg bg-brand-600 px-6 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition"
        >
          {submitting ? "Creating..." : "Create Analysis"}
        </button>
      </form>
    </div>
  );
}
