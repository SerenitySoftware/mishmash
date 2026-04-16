"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface StarButtonProps {
  targetType: "dataset" | "analysis";
  targetId: string;
  initialStarCount: number;
}

export function StarButton({ targetType, targetId, initialStarCount }: StarButtonProps) {
  const { user } = useAuth();
  const [starred, setStarred] = useState(false);
  const [starCount, setStarCount] = useState(initialStarCount);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) return;
    apiFetch<{ starred: boolean }>(`/api/stars/${targetType}/${targetId}/check`)
      .then((data) => setStarred(data.starred))
      .catch(() => {});
  }, [user, targetType, targetId]);

  const toggle = async () => {
    if (!user || loading) return;
    setLoading(true);
    try {
      if (starred) {
        const resp = await apiFetch<{ star_count: number }>(
          `/api/stars/${targetType}/${targetId}`,
          { method: "DELETE" }
        );
        setStarred(false);
        setStarCount(resp.star_count);
      } else {
        const resp = await apiFetch<{ star_count: number }>(
          `/api/stars/${targetType}/${targetId}`,
          { method: "POST" }
        );
        setStarred(true);
        setStarCount(resp.star_count);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={toggle}
      disabled={!user || loading}
      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-sm font-medium transition ${
        starred
          ? "border-yellow-300 bg-yellow-50 text-yellow-700"
          : "border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
      } disabled:opacity-50`}
    >
      <span>{starred ? "\u2605" : "\u2606"}</span>
      <span>{starCount}</span>
    </button>
  );
}
