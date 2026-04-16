"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type DatasetList } from "@/lib/api";
import { DatasetCard } from "@/components/DatasetCard";
import { useAuth } from "@/lib/auth";

export default function DatasetsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DatasetList | null>(null);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("updated");
  const [loading, setLoading] = useState(true);

  const fetchDatasets = async (q?: string, s?: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      params.set("sort", s || sort);
      const result = await apiFetch<DatasetList>(`/api/datasets?${params.toString()}`);
      setData(result);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchDatasets(); }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDatasets(search, sort);
  };

  const handleSortChange = (newSort: string) => {
    setSort(newSort);
    fetchDatasets(search, newSort);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Datasets</h1>
        {user && (
          <Link href="/datasets/new" className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 transition">
            Upload Dataset
          </Link>
        )}
      </div>

      <div className="flex gap-3">
        <form onSubmit={handleSearch} className="flex gap-2 flex-1">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search datasets..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
          />
          <button type="submit" className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 transition">
            Search
          </button>
        </form>
        <select
          value={sort}
          onChange={(e) => handleSortChange(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 outline-none"
        >
          <option value="updated">Recently Updated</option>
          <option value="created">Newest</option>
          <option value="stars">Most Stars</option>
          <option value="downloads">Most Downloads</option>
        </select>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4">
          {data.items.map((ds) => <DatasetCard key={ds.id} dataset={ds} />)}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          {search ? "No datasets match your search." : "No datasets found. Be the first to upload one!"}
        </div>
      )}

      {data && data.total > data.page_size && (
        <div className="text-center text-sm text-gray-500">
          Showing {data.items.length} of {data.total} datasets
        </div>
      )}
    </div>
  );
}
