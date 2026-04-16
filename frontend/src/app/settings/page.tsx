"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
}

export default function SettingsPage() {
  const router = useRouter();
  const { user, loading: authLoading, refreshUser } = useAuth();
  const [name, setName] = useState("");
  const [bio, setBio] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // API keys
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyValue, setNewKeyValue] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      setName(user.name);
      setBio(user.bio || "");
      apiFetch<ApiKey[]>("/api/keys").then(setApiKeys).catch(() => {});
    }
  }, [user]);

  if (!user) return null;

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch("/api/auth/me", {
        method: "PUT",
        body: JSON.stringify({ name, bio: bio || null }),
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setSaving(false);
    }
  };

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const resp = await apiFetch<{ id: string; name: string; key: string; key_prefix: string }>(
        "/api/keys",
        { method: "POST", body: JSON.stringify({ name: newKeyName }) }
      );
      setNewKeyValue(resp.key);
      setNewKeyName("");
      setApiKeys(await apiFetch<ApiKey[]>("/api/keys"));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Failed to create API key");
    }
  };

  const handleRevokeKey = async (id: string) => {
    await apiFetch(`/api/keys/${id}`, { method: "DELETE" });
    setApiKeys(await apiFetch<ApiKey[]>("/api/keys"));
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Account Settings</h1>

      {/* Profile */}
      <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold">Profile</h2>
        <form onSubmit={handleSaveProfile} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bio</label>
            <textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none"
              placeholder="Tell others about yourself..." />
          </div>
          <div className="flex items-center gap-3">
            <button type="submit" disabled={saving}
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 disabled:opacity-50 transition">
              {saving ? "Saving..." : "Save Profile"}
            </button>
            {saved && <span className="text-sm text-green-600">Saved!</span>}
          </div>
        </form>
        <div className="pt-2 border-t border-gray-100">
          <p className="text-sm text-gray-500">Username: @{user.username} (cannot be changed)</p>
          <p className="text-sm text-gray-500">Email: {user.email}</p>
        </div>
      </section>

      {/* API Keys */}
      <section className="bg-white rounded-xl border border-gray-200 p-6 space-y-4">
        <h2 className="text-lg font-semibold">API Keys</h2>
        <p className="text-sm text-gray-600">
          Use API keys for programmatic access. Include the key in the Authorization header: <code className="bg-gray-100 px-1 rounded">Bearer msh_...</code>
        </p>

        {newKeyValue && (
          <div className="rounded-lg bg-green-50 border border-green-200 p-4">
            <p className="text-sm font-medium text-green-800 mb-1">API key created! Copy it now — it won't be shown again:</p>
            <code className="block bg-green-100 rounded p-2 text-sm break-all">{newKeyValue}</code>
            <button onClick={() => setNewKeyValue(null)} className="mt-2 text-xs text-green-600">Dismiss</button>
          </div>
        )}

        <form onSubmit={handleCreateKey} className="flex gap-2">
          <input type="text" value={newKeyName} onChange={(e) => setNewKeyName(e.target.value)}
            placeholder="Key name (e.g. 'CI Pipeline')"
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 outline-none" />
          <button type="submit" className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium hover:bg-gray-200 transition">
            Create Key
          </button>
        </form>

        {apiKeys.length > 0 && (
          <div className="divide-y divide-gray-100">
            {apiKeys.map((key) => (
              <div key={key.id} className="flex items-center justify-between py-3">
                <div>
                  <span className="font-medium text-sm">{key.name}</span>
                  <span className="ml-2 text-xs text-gray-400">{key.key_prefix}...</span>
                  {!key.is_active && <span className="ml-2 text-xs text-red-500">revoked</span>}
                </div>
                {key.is_active && (
                  <button onClick={() => handleRevokeKey(key.id)}
                    className="text-xs text-red-500 hover:text-red-700">Revoke</button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
