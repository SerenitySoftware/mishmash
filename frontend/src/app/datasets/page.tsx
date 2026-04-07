"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type DatasetList } from "@/lib/api";
import { DatasetCard } from "@/components/DatasetCard";

export default function DatasetsPage() {
  const [data, setData] = useState<DatasetList | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchDatasets = async (q?: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      const result = await apiFetch<DatasetList>(
        `/api/datasets?${params.toString()}`
      );
      setData(result);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchDatasets(search);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Datasets</h1>
        <Link
          href="/datasets/new"
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 transition"
        >
          Upload Dataset
        </Link>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search datasets..."
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
        />
        <button
          type="submit"
          className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 transition"
        >
          Search
        </button>
      </form>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4">
          {data.items.map((ds) => (
            <DatasetCard key={ds.id} dataset={ds} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          No datasets found. Be the first to upload one!
        </div>
      )}
    </div>
  );
}
