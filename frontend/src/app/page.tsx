"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiFetch, type DatasetList, type AnalysisList, type PublicationList } from "@/lib/api";
import { DatasetCard } from "@/components/DatasetCard";
import { useAuth } from "@/lib/auth";

export default function Home() {
  const { user } = useAuth();
  const [recentDatasets, setRecentDatasets] = useState<DatasetList | null>(null);
  const [popularDatasets, setPopularDatasets] = useState<DatasetList | null>(null);
  const [recentAnalyses, setRecentAnalyses] = useState<AnalysisList | null>(null);

  useEffect(() => {
    apiFetch<DatasetList>("/api/datasets?page_size=6&sort=created").then(setRecentDatasets).catch(() => {});
    apiFetch<DatasetList>("/api/datasets?page_size=6&sort=stars").then(setPopularDatasets).catch(() => {});
    apiFetch<AnalysisList>("/api/analyses?page_size=4&sort=stars").then(setRecentAnalyses).catch(() => {});
  }, []);

  return (
    <div className="space-y-12">
      {/* Hero */}
      <section className="text-center py-16">
        <h1 className="text-5xl font-bold tracking-tight text-gray-900">Mishmash</h1>
        <p className="mt-4 text-xl text-gray-600 max-w-2xl mx-auto">
          The open platform for collaborative data analysis. Upload datasets, run reproducible analyses, and share your findings with the world.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          {user ? (
            <>
              <Link href="/datasets/new" className="rounded-lg bg-brand-600 px-6 py-3 text-white font-medium hover:bg-brand-700 transition">
                Upload Dataset
              </Link>
              <Link href="/analyses/new" className="rounded-lg border border-gray-300 px-6 py-3 font-medium hover:bg-gray-100 transition">
                Create Analysis
              </Link>
            </>
          ) : (
            <>
              <Link href="/register" className="rounded-lg bg-brand-600 px-6 py-3 text-white font-medium hover:bg-brand-700 transition">
                Get Started
              </Link>
              <Link href="/datasets" className="rounded-lg border border-gray-300 px-6 py-3 font-medium hover:bg-gray-100 transition">
                Browse Datasets
              </Link>
            </>
          )}
        </div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <FeatureCard title="Upload & Version" description="Upload CSV, JSON, or Parquet datasets. Every change is versioned, forkable, and downloadable." />
        <FeatureCard title="Analyze & Reproduce" description="Write Python or R scripts that run in sandboxed environments. Every result is reproducible." />
        <FeatureCard title="Prove Your Work" description="Run analyses locally with cryptographic proof-of-work. Anyone can verify your computation." />
        <FeatureCard title="Share & Discuss" description="Publish findings linked to source data. Star, fork, comment, and build on each other's work." />
      </section>

      {/* Popular datasets */}
      {popularDatasets && popularDatasets.items.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Popular Datasets</h2>
            <Link href="/datasets?sort=stars" className="text-sm text-brand-600 hover:text-brand-800">View all</Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {popularDatasets.items.slice(0, 4).map((ds) => <DatasetCard key={ds.id} dataset={ds} />)}
          </div>
        </section>
      )}

      {/* Recent datasets */}
      {recentDatasets && recentDatasets.items.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Recently Added</h2>
            <Link href="/datasets" className="text-sm text-brand-600 hover:text-brand-800">View all</Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {recentDatasets.items.slice(0, 4).map((ds) => <DatasetCard key={ds.id} dataset={ds} />)}
          </div>
        </section>
      )}

      {/* Recent analyses */}
      {recentAnalyses && recentAnalyses.items.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">Top Analyses</h2>
            <Link href="/analyses" className="text-sm text-brand-600 hover:text-brand-800">View all</Link>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {recentAnalyses.items.map((a) => (
              <Link key={a.id} href={`/analyses/${a.id}`}
                className="block rounded-lg border border-gray-200 bg-white p-5 shadow-sm hover:shadow-md transition">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold">{a.title}</h3>
                    {a.owner && <p className="text-xs text-gray-500">by @{a.owner.username}</p>}
                  </div>
                  <span className="rounded bg-gray-100 px-2 py-0.5 text-xs font-medium uppercase">{a.language}</span>
                </div>
                <div className="mt-2 text-xs text-gray-500">{a.star_count} stars / {a.fork_count} forks</div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* How it works */}
      <section className="bg-white rounded-xl p-8 shadow-sm border border-gray-200">
        <h2 className="text-2xl font-bold text-center mb-8">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
          <Step number={1} title="Upload" description="Drop your dataset files" />
          <Step number={2} title="Analyze" description="Write code to process the data" />
          <Step number={3} title="Verify" description="Run locally with proof-of-work" />
          <Step number={4} title="Connect" description="Link and cross-reference datasets" />
          <Step number={5} title="Publish" description="Share findings with provenance" />
        </div>
      </section>

      {/* CLI callout */}
      <section className="bg-gray-900 text-white rounded-xl p-8">
        <h2 className="text-xl font-bold mb-3">Run from your terminal</h2>
        <p className="text-gray-400 mb-4">
          Install the Mishmash CLI to upload datasets, run analyses locally with proof-of-work, and manage your work from the command line.
        </p>
        <pre className="bg-gray-800 rounded-lg p-4 text-sm overflow-x-auto">
          <code>pip install mishmash-cli{"\n"}mishmash register{"\n"}mishmash upload data.csv --name "My Dataset"{"\n"}mishmash run &lt;analysis-id&gt;</code>
        </pre>
      </section>
    </div>
  );
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-200">
      <h3 className="text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-gray-600 text-sm">{description}</p>
    </div>
  );
}

function Step({ number, title, description }: { number: number; title: string; description: string }) {
  return (
    <div className="text-center">
      <div className="mx-auto w-10 h-10 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-bold text-lg">{number}</div>
      <h3 className="mt-3 font-semibold">{title}</h3>
      <p className="mt-1 text-sm text-gray-600">{description}</p>
    </div>
  );
}
