"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

interface HistoryEntry {
  id: string;
  media_type: string;
  prompt_or_text: string;
  voice: string | null;
  url: string;
  created_at: string;
}

export default function HistoryPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [filter, setFilter] = useState<"all" | "image" | "speech">("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadHistory() {
    setLoading(true);
    setError("");
    try {
      const token = getToken();
      const params = filter !== "all" ? `?media_type=${filter}` : "";
      const data = await apiFetch(`/history${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEntries(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load history.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="border-b border-neutral-800 px-6 py-4 flex items-center justify-between">
        <button
          onClick={() => router.push("/dashboard")}
          className="text-sm text-neutral-400 hover:text-white transition"
        >
          ← Back to Dashboard
        </button>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold mb-6">Generation History</h1>

        <div className="flex gap-2 mb-8 bg-neutral-900 border border-neutral-800 rounded-lg p-1 w-fit">
          {(["all", "image", "speech"] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition capitalize ${
                filter === f ? "bg-white text-black" : "text-neutral-400 hover:text-white"
              }`}
            >
              {f === "all" ? "All" : f === "image" ? "Images" : "Speech"}
            </button>
          ))}
        </div>

        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2 mb-6">
            {error}
          </p>
        )}

        {loading ? (
          <p className="text-neutral-500 text-sm">Loading...</p>
        ) : entries.length === 0 ? (
          <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center text-neutral-500">
            No history yet.
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <div
                key={entry.id}
                className="rounded-xl border border-neutral-800 bg-neutral-950 p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs px-2 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-400 capitalize">
                    {entry.media_type}
                    {entry.voice ? ` · ${entry.voice}` : ""}
                  </span>
                  <span className="text-xs text-neutral-600">
                    {new Date(entry.created_at).toLocaleString()}
                  </span>
                </div>
                <p className="text-sm text-neutral-300 mb-3">{entry.prompt_or_text}</p>
                {entry.media_type === "image" ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={entry.url} alt={entry.prompt_or_text} className="rounded-lg max-w-sm" />
                ) : (
                  <audio controls className="w-full" src={entry.url} />
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}