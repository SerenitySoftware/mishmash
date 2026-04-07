"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type AnalysisList } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function AnalysesPage() {
  const { user } = useAuth();
  const [data, setData] = useState<AnalysisList | null>(null);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("updated");
  const [language, setLanguage] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchAnalyses = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("q", search);
      if (language) params.set("language", language);
      params.set("sort", sort);
      const result = await apiFetch<AnalysisList>(`/api/analyses?${params.toString()}`);
      setData(result);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAnalyses(); }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchAnalyses();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Analyses</h1>
        {user && (
          <Link href="/analyses/new" className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 transition">
            New Analysis
          </Link>
        )}
      </div>

      <div className="flex gap-3">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1">
          <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search analyses..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
          <button type="submit" className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 transition">Search</button>
        </form>
        <select value={language} onChange={(e) => { setLanguage(e.target.value); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 outline-none">
          <option value="">All Languages</option>
          <option value="python">Python</option>
          <option value="r">R</option>
          <option value="sql">SQL</option>
        </select>
        <select value={sort} onChange={(e) => { setSort(e.target.value); }}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 outline-none">
          <option value="updated">Recently Updated</option>
          <option value="created">Newest</option>
          <option value="stars">Most Stars</option>
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4">
          {data.items.map((analysis) => (
            <Link key={analysis.id} href={`/analyses/${analysis.id}`}
              className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold">{analysis.title}</h3>
                    {analysis.forked_from_id && <span className="text-xs text-gray-400">forked</span>}
                  </div>
                  {analysis.owner && <p className="text-xs text-gray-500">by @{analysis.owner.username}</p>}
                  {analysis.description && <p className="mt-1 text-sm text-gray-600 line-clamp-2">{analysis.description}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium uppercase">{analysis.language}</span>
                  <span className={`rounded px-2 py-0.5 text-xs font-medium ${
                    analysis.status === "completed" ? "bg-green-100 text-green-700" :
                    analysis.status === "failed" ? "bg-red-100 text-red-700" :
                    analysis.status === "running" ? "bg-yellow-100 text-yellow-700" :
                    "bg-gray-100 text-gray-700"
                  }`}>{analysis.status}</span>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                <span>{analysis.star_count} stars</span>
                <span>{analysis.fork_count} forks</span>
                <span>{analysis.datasets.length} dataset(s)</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          {search ? "No analyses match your search." : "No analyses yet. Create one to get started!"}
        </div>
      )}
    </div>
  );
}
