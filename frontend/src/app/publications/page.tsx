"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch, type PublicationList } from "@/lib/api";

export default function PublicationsPage() {
  const [data, setData] = useState<PublicationList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<PublicationList>("/api/publications")
      .then(setData)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Publications</h1>
        <Link
          href="/publications/new"
          className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 transition"
        >
          New Publication
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : data && data.items.length > 0 ? (
        <div className="grid gap-4">
          {data.items.map((pub) => (
            <Link
              key={pub.id}
              href={`/publications/${pub.slug}`}
              className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition"
            >
              <h3 className="font-semibold text-lg">{pub.title}</h3>
              <p className="mt-1 text-sm text-gray-600 line-clamp-3">
                {pub.body.slice(0, 200)}...
              </p>
              <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                <span>{pub.references.length} reference(s)</span>
                <span>{new Date(pub.created_at).toLocaleDateString()}</span>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          No publications yet. Share your findings!
        </div>
      )}
    </div>
  );
}
