"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { apiFetch, type Publication, type Comment } from "@/lib/api";
import { CommentThread } from "@/components/CommentThread";

export default function PublicationDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [pub, setPub] = useState<Publication | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const p = await apiFetch<Publication>(`/api/publications/${slug}`);
      setPub(p);
      const c = await apiFetch<Comment[]>(
        `/api/comments?target_type=publication&target_id=${p.id}`
      );
      setComments(c);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (!pub) return <div className="text-center py-12 text-gray-500">Publication not found</div>;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <header>
        <h1 className="text-3xl font-bold">{pub.title}</h1>
        <div className="mt-2 text-sm text-gray-500">
          Published {new Date(pub.created_at).toLocaleDateString()}
          {pub.references.length > 0 && (
            <span className="ml-3">
              {pub.references.length} linked reference(s)
            </span>
          )}
        </div>
      </header>

      {/* References */}
      {pub.references.length > 0 && (
        <div className="rounded-lg bg-brand-50 border border-brand-200 p-4">
          <h3 className="text-sm font-medium text-brand-800 mb-2">
            Linked References
          </h3>
          <ul className="space-y-1">
            {pub.references.map((ref) => (
              <li key={`${ref.ref_type}-${ref.ref_id}`} className="text-sm text-brand-700">
                {ref.ref_type}: {ref.ref_id}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Body */}
      <article className="prose prose-gray max-w-none">
        <ReactMarkdown>{pub.body}</ReactMarkdown>
      </article>

      {/* Comments */}
      <CommentThread
        targetType="publication"
        targetId={pub.id}
        comments={comments}
        onRefresh={fetchData}
      />
    </div>
  );
}
