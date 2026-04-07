"use client";

import { useState } from "react";
import { apiFetch, type Comment } from "@/lib/api";

interface CommentThreadProps {
  targetType: string;
  targetId: string;
  comments: Comment[];
  onRefresh: () => void;
}

export function CommentThread({
  targetType,
  targetId,
  comments,
  onRefresh,
}: CommentThreadProps) {
  return (
    <div className="space-y-4">
      <h3 className="font-semibold text-lg">
        Comments ({comments.length})
      </h3>
      <CommentForm
        targetType={targetType}
        targetId={targetId}
        onSubmit={onRefresh}
      />
      <div className="space-y-3">
        {comments.map((comment) => (
          <CommentItem
            key={comment.id}
            comment={comment}
            targetType={targetType}
            targetId={targetId}
            onRefresh={onRefresh}
          />
        ))}
      </div>
    </div>
  );
}

function CommentItem({
  comment,
  targetType,
  targetId,
  onRefresh,
  depth = 0,
}: {
  comment: Comment;
  targetType: string;
  targetId: string;
  onRefresh: () => void;
  depth?: number;
}) {
  const [replying, setReplying] = useState(false);

  return (
    <div className={depth > 0 ? "ml-6 border-l-2 border-gray-100 pl-4" : ""}>
      <div className="rounded-lg bg-white border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="font-medium text-gray-700">
            {comment.author_id.slice(0, 8)}
          </span>
          <span>{new Date(comment.created_at).toLocaleDateString()}</span>
        </div>
        <p className="mt-2 text-sm text-gray-700 whitespace-pre-wrap">
          {comment.body}
        </p>
        <button
          onClick={() => setReplying(!replying)}
          className="mt-2 text-xs text-brand-600 hover:text-brand-800"
        >
          {replying ? "Cancel" : "Reply"}
        </button>
      </div>
      {replying && (
        <div className="ml-6 mt-2">
          <CommentForm
            targetType={targetType}
            targetId={targetId}
            parentId={comment.id}
            onSubmit={() => {
              setReplying(false);
              onRefresh();
            }}
          />
        </div>
      )}
      {comment.replies?.map((reply) => (
        <CommentItem
          key={reply.id}
          comment={reply}
          targetType={targetType}
          targetId={targetId}
          onRefresh={onRefresh}
          depth={depth + 1}
        />
      ))}
    </div>
  );
}

function CommentForm({
  targetType,
  targetId,
  parentId,
  onSubmit,
}: {
  targetType: string;
  targetId: string;
  parentId?: string;
  onSubmit: () => void;
}) {
  const [body, setBody] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!body.trim()) return;
    setSubmitting(true);
    try {
      await apiFetch("/api/comments", {
        method: "POST",
        body: JSON.stringify({
          target_type: targetType,
          target_id: targetId,
          parent_id: parentId || null,
          body: body.trim(),
        }),
      });
      setBody("");
      onSubmit();
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder="Add a comment..."
        className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
        disabled={submitting}
      />
      <button
        type="submit"
        disabled={submitting || !body.trim()}
        className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition"
      >
        Post
      </button>
    </form>
  );
}
