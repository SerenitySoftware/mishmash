"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type AnalysisList } from "@/lib/api";

export default function AnalysesPage() {
  const [data, setData] = useState<AnalysisList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<AnalysisList>("/api/analyses")
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Analyses</h1>
        <Link
          href="/analyses/new"
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 transition"
        >
          New Analysis
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4">
          {data.items.map((analysis) => (
            <Link
              key={analysis.id}
              href={`/analyses/${analysis.id}`}
              className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{analysis.title}</h3>
                  {analysis.description && (
                    <p className="mt-1 text-sm text-gray-600 line-clamp-2">
                      {analysis.description}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium uppercase">
                    {analysis.language}
                  </span>
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      analysis.status === "completed"
                        ? "bg-green-100 text-green-700"
                        : analysis.status === "failed"
                        ? "bg-red-100 text-red-700"
                        : analysis.status === "running"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {analysis.status}
                  </span>
                </div>
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {analysis.datasets.length} dataset(s) linked
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          No analyses yet. Create one to get started!
        </div>
      )}
    </div>
  );
}
