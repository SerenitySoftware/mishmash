"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, type Dataset } from "@/lib/api";
import { FileUploader } from "@/components/FileUploader";
import { useAuth } from "@/lib/auth";

export default function NewDatasetPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [format, setFormat] = useState("csv");
  const [license, setLicense] = useState("");
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [step, setStep] = useState<"info" | "upload">("info");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  if (!user) return null;

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const ds = await apiFetch<Dataset>("/api/datasets", {
        method: "POST",
        body: JSON.stringify({
          name,
          description: description || null,
          tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
          format,
          license: license || null,
        }),
      });
      setDataset(ds);
      setStep("upload");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create dataset");
    }
  };

  const handleUpload = async (file: File) => {
    if (!dataset) return;
    const { upload_url, storage_key } = await apiFetch<{ upload_url: string; storage_key: string }>(
      `/api/datasets/${dataset.id}/upload?filename=${encodeURIComponent(file.name)}`,
      { method: "POST" }
    );
    await fetch(upload_url, { method: "PUT", body: file, headers: { "Content-Type": "application/octet-stream" } });
    await apiFetch(`/api/datasets/${dataset.id}/upload/complete`, {
      method: "POST",
      body: JSON.stringify({ dataset_id: dataset.id, storage_key, file_size_bytes: file.size }),
    });
    router.push(`/datasets/${dataset.slug}`);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Upload New Dataset</h1>

      {step === "info" && (
        <form onSubmit={handleCreate} className="space-y-4 bg-white p-6 rounded-xl border border-gray-200">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" placeholder="My Dataset" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" placeholder="What is this dataset about?" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Format</label>
              <select value={format} onChange={(e) => setFormat(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                <option value="csv">CSV</option>
                <option value="json">JSON (newline-delimited)</option>
                <option value="parquet">Parquet</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">License</label>
              <select value={license} onChange={(e) => setLicense(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none">
                <option value="">None specified</option>
                <option value="CC0-1.0">CC0 (Public Domain)</option>
                <option value="CC-BY-4.0">CC BY 4.0</option>
                <option value="CC-BY-SA-4.0">CC BY-SA 4.0</option>
                <option value="ODbL-1.0">ODbL 1.0</option>
                <option value="MIT">MIT</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tags (comma-separated)</label>
            <input type="text" value={tags} onChange={(e) => setTags(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" placeholder="economics, demographics, 2024" />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button type="submit" className="rounded-lg bg-brand-600 px-6 py-2 text-white font-medium hover:bg-brand-700 transition">
            Continue to Upload
          </button>
        </form>
      )}

      {step === "upload" && dataset && (
        <div className="space-y-4">
          <p className="text-gray-600">
            Dataset <strong>{dataset.name}</strong> created. Now upload your {format.toUpperCase()} file:
          </p>
          <FileUploader onUpload={handleUpload} />
        </div>
      )}
    </div>
  );
}
