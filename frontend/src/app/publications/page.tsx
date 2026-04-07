"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type PublicationList } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function PublicationsPage() {
  const { user } = useAuth();
  const [data, setData] = useState<PublicationList | null>(null);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchPubs = async (q?: string) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      const result = await apiFetch<PublicationList>(`/api/publications?${params.toString()}`);
      setData(result);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPubs(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Publications</h1>
        {user && (
          <Link href="/publications/new" className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 transition">
            New Publication
          </Link>
        )}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); fetchPubs(search); }} className="flex gap-2">
        <input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search publications..."
          className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
        <button type="submit" className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 transition">Search</button>
      </form>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4">
          {data.items.map((pub) => (
            <Link key={pub.id} href={`/publications/${pub.slug}`}
              className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition">
              <h3 className="font-semibold text-lg">{pub.title}</h3>
              <p className="mt-1 text-sm text-gray-600 line-clamp-3">{pub.body.slice(0, 200)}...</p>
              <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                <span>{pub.references.length} reference(s)</span>
                <span>{new Date(pub.created_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          {search ? "No publications match your search." : "No publications yet. Share your findings!"}
        </div>
      )}
    </div>
  );
}
