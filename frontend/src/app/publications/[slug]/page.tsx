"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import { apiFetch, type Comment } from "@/lib/api";
import { CommentThread } from "@/components/CommentThread";
import { useAuth } from "@/lib/auth";

interface PublicationDetail {
  id: string;
  author_id: string;
  author: { id: string; username: string; name: string; avatar_url: string | null } | null;
  title: string;
  slug: string;
  body: string;
  references: { ref_type: string; ref_id: string }[];
  created_at: string;
  updated_at: string;
}

export default function PublicationDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { user } = useAuth();

  const [pub, setPub] = useState<PublicationDetail | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [editBody, setEditBody] = useState("");

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const p = await apiFetch<PublicationDetail>(`/api/publications/${slug}`);
      setPub(p);
      setEditBody(p.body);
      const c = await apiFetch<Comment[]>(`/api/comments?target_type=publication&target_id=${p.id}`);
      setComments(c);
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleSave = async () => {
    if (!pub) return;
    await apiFetch(`/api/publications/${pub.id}`, {
      method: "PUT",
      body: JSON.stringify({ body: editBody }),
    });
    setEditing(false);
    fetchData();
  };

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (!pub) return <div className="text-center py-12 text-gray-500">Publication not found</div>;

  const isAuthor = user && user.id === pub.author_id;

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <header>
        <h1 className="text-3xl font-bold">{pub.title}</h1>
        <div className="mt-2 flex items-center gap-3 text-sm text-gray-500">
          {pub.author && (
            <Link href={`/u/${pub.author.username}`} className="font-medium text-gray-700 hover:text-brand-600">
              by {pub.author.name} (@{pub.author.username})
            </Link>
          )}
          <span>Published {new Date(pub.created_at).toLocaleDateString()}</span>
          {pub.references.length > 0 && <span>{pub.references.length} linked reference(s)</span>}
        </div>
        {isAuthor && (
          <div className="mt-3">
            {editing ? (
              <div className="flex gap-2">
                <button onClick={handleSave} className="rounded-lg bg-brand-600 px-3 py-1 text-sm text-white hover:bg-brand-700 transition">Save</button>
                <button onClick={() => { setEditing(false); setEditBody(pub.body); }} className="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 transition">Cancel</button>
              </div>
            ) : (
              <button onClick={() => setEditing(true)} className="rounded-lg border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 transition">Edit</button>
            )}
          </div>
        )}
      </header>

      {/* References */}
      {pub.references.length > 0 && (
        <div className="rounded-lg bg-brand-50 border border-brand-200 p-4">
          <h3 className="text-sm font-medium text-brand-800 mb-2">Linked References</h3>
          <ul className="space-y-1">
            {pub.references.map((ref) => (
              <li key={`${ref.ref_type}-${ref.ref_id}`} className="text-sm">
                <Link
                  href={ref.ref_type === "dataset" ? `/datasets/${ref.ref_id}` : `/analyses/${ref.ref_id}`}
                  className="text-brand-700 hover:text-brand-900"
                >
                  {ref.ref_type}: {ref.ref_id.slice(0, 12)}...
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Body */}
      {editing ? (
        <textarea value={editBody} onChange={(e) => setEditBody(e.target.value)} rows={30}
          className="w-full rounded-lg border border-gray-300 px-3 py-2 font-mono text-sm focus:border-brand-500 outline-none" />
      ) : (
        <article className="prose prose-gray max-w-none">
          <ReactMarkdown>{pub.body}</ReactMarkdown>
        </article>
      )}

      {/* Comments */}
      <CommentThread targetType="publication" targetId={pub.id} comments={comments} onRefresh={fetchData} />
    </div>
  );
}
