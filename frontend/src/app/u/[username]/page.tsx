"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { apiFetch, type UserProfile, type DatasetList, type AnalysisList, type PublicationList } from "@/lib/api";

export default function ProfilePage() {
  const params = useParams();
  const username = params.username as string;

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [activeTab, setActiveTab] = useState<"datasets" | "analyses" | "publications">("datasets");
  const [datasets, setDatasets] = useState<DatasetList | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisList | null>(null);
  const [publications, setPublications] = useState<PublicationList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      apiFetch<UserProfile>(`/api/users/${username}`),
      apiFetch<DatasetList>(`/api/users/${username}/datasets`),
      apiFetch<AnalysisList>(`/api/users/${username}/analyses`),
      apiFetch<PublicationList>(`/api/users/${username}/publications`),
    ])
      .then(([p, d, a, pub]) => {
        setProfile(p);
        setDatasets(d);
        setAnalyses(a);
        setPublications(pub);
      })
      .finally(() => setLoading(false));
  }, [username]);

  if (loading) return <div className="text-center py-12 text-gray-500">Loading...</div>;
  if (!profile) return <div className="text-center py-12 text-gray-500">User not found</div>;

  const tabs = [
    { key: "datasets" as const, label: "Datasets", count: profile.dataset_count },
    { key: "analyses" as const, label: "Analyses", count: profile.analysis_count },
    { key: "publications" as const, label: "Publications", count: profile.publication_count },
  ];

  return (
    <div className="space-y-6">
      {/* Profile header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-full bg-brand-100 flex items-center justify-center text-2xl font-bold text-brand-700">
            {profile.name[0].toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl font-bold">{profile.name}</h1>
            <p className="text-gray-500">@{profile.username}</p>
            {profile.bio && <p className="mt-2 text-gray-700">{profile.bio}</p>}
            <p className="mt-2 text-sm text-gray-400">
              Joined {new Date(profile.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-2 px-1 border-b-2 text-sm font-medium transition ${
                activeTab === tab.key
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {activeTab === "datasets" && datasets && (
        <div className="grid gap-4">
          {datasets.items.length === 0 && (
            <p className="text-center py-8 text-gray-500">No datasets yet</p>
          )}
          {datasets.items.map((ds) => (
            <Link
              key={ds.id}
              href={`/datasets/${ds.slug}`}
              className="block rounded-lg border border-gray-200 bg-white p-4 hover:shadow-md transition"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{ds.name}</h3>
                  {ds.description && (
                    <p className="mt-1 text-sm text-gray-600 line-clamp-2">{ds.description}</p>
                  )}
                </div>
                <span className="text-xs bg-gray-100 px-2 py-0.5 rounded uppercase">{ds.format}</span>
              </div>
              <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                {ds.row_count && <span>{ds.row_count.toLocaleString()} rows</span>}
                <span>{ds.star_count} stars</span>
                <span>{ds.fork_count} forks</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {activeTab === "analyses" && analyses && (
        <div className="grid gap-4">
          {analyses.items.length === 0 && (
            <p className="text-center py-8 text-gray-500">No analyses yet</p>
          )}
          {analyses.items.map((a) => (
            <Link
              key={a.id}
              href={`/analyses/${a.id}`}
              className="block rounded-lg border border-gray-200 bg-white p-4 hover:shadow-md transition"
            >
              <div className="flex items-start justify-between">
                <h3 className="font-semibold">{a.title}</h3>
                <div className="flex gap-2">
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded uppercase">{a.language}</span>
                  <span className="text-xs bg-gray-100 px-2 py-0.5 rounded">{a.status}</span>
                </div>
              </div>
              <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                <span>{a.star_count} stars</span>
                <span>{a.datasets.length} datasets</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {activeTab === "publications" && publications && (
        <div className="grid gap-4">
          {publications.items.length === 0 && (
            <p className="text-center py-8 text-gray-500">No publications yet</p>
          )}
          {publications.items.map((pub) => (
            <Link
              key={pub.id}
              href={`/publications/${pub.slug}`}
              className="block rounded-lg border border-gray-200 bg-white p-4 hover:shadow-md transition"
            >
              <h3 className="font-semibold">{pub.title}</h3>
              <p className="mt-1 text-sm text-gray-600 line-clamp-2">{pub.body.slice(0, 200)}</p>
              <div className="mt-2 text-xs text-gray-500">
                {new Date(pub.created_at).toLocaleDateString()}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
