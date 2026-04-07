"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, type Publication } from "@/lib/api";

export default function NewPublicationPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const pub = await apiFetch<Publication>("/api/publications", {
        method: "POST",
        body: JSON.stringify({
          title,
          body,
          references: [],
        }),
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
            placeholder="My Research Findings"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Body (Markdown)
          </label>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            required
            rows={20}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
            placeholder={`## Summary\n\nDescribe your findings...\n\n## Methodology\n\n## Results\n\n## Conclusion`}
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting || !title.trim() || !body.trim()}
          className="rounded-lg bg-brand-600 px-6 py-2 text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition"
        >
          {submitting ? "Publishing..." : "Publish"}
        </button>
      </form>
    </div>
  );
}
