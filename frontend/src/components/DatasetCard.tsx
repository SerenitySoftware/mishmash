import Link from "next/link";
import type { Dataset } from "@/lib/api";

export function DatasetCard({ dataset }: { dataset: Dataset }) {
  return (
    <Link
      href={`/datasets/${dataset.slug}`}
      className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition"
    >
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">{dataset.name}</h3>
            {dataset.forked_from_id && (
              <span className="text-xs text-gray-400">forked</span>
            )}
          </div>
          {dataset.owner && (
            <p className="text-xs text-gray-500">by @{dataset.owner.username}</p>
          )}
          {dataset.description && (
            <p className="mt-1 text-sm text-gray-600 line-clamp-2">
              {dataset.description}
            </p>
          )}
        </div>
        <span className="ml-2 inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700 uppercase">
          {dataset.format}
        </span>
      </div>
      <div className="mt-3 flex items-center gap-4 text-xs text-gray-500">
        {dataset.row_count !== null && (
          <span>{dataset.row_count.toLocaleString()} rows</span>
        )}
        <span>v{dataset.current_version}</span>
        <span>{dataset.star_count} stars</span>
        <span>{dataset.fork_count} forks</span>
        <span>{dataset.download_count} downloads</span>
        {dataset.tags.length > 0 && (
          <div className="flex gap-1">
            {dataset.tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="rounded bg-brand-50 px-1.5 py-0.5 text-brand-700"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
    </Link>
  );
}
