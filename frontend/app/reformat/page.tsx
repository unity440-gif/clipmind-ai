"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function ReformatPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const [error, setError] = useState("");

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResultUrl(null);

    if (!file) {
      setError("Please choose a video file.");
      return;
    }

    setLoading(true);

    try {
      const token = getToken();
      const formData = new FormData();
      formData.append("aspect_ratio", aspectRatio);
      formData.append("file", file);

      const response = await fetch(`${API_URL}/reformat/video`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        const errBody = await response.json().catch(() => null);
        throw new Error(errBody?.detail || "Reformat failed.");
      }

      const data = await response.json();
      setResultUrl(data.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

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

      <main className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold mb-2">Quick Reformat</h1>
        <p className="text-neutral-500 text-sm mb-8">
          Upload a full video and get it back in a different aspect ratio — no clipping, no AI, free.
        </p>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`rounded-xl border-2 border-dashed px-6 py-12 text-center cursor-pointer transition ${
              dragActive
                ? "border-white bg-neutral-900"
                : "border-neutral-800 hover:border-neutral-700"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".mp4,.mov,.avi,.mkv"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            {file ? (
              <p className="text-neutral-300">{file.name}</p>
            ) : (
              <p className="text-neutral-400">Drag and drop a video, or click to browse</p>
            )}
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">Target aspect ratio</label>
            <select
              value={aspectRatio}
              onChange={(e) => setAspectRatio(e.target.value)}
              className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
            >
              <option value="9:16">9:16 (Vertical)</option>
              <option value="16:9">16:9 (Landscape)</option>
              <option value="1:1">1:1 (Square)</option>
            </select>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-white text-black text-sm font-medium px-5 py-2.5 hover:bg-neutral-200 transition disabled:opacity-50"
          >
            {loading ? "Processing... (this can take a bit for longer videos)" : "Reformat Video"}
          </button>
        </form>

        {resultUrl && (
          <div className="mt-8 rounded-xl border border-neutral-800 bg-neutral-950 p-5">
            <video controls className="w-full rounded-lg" src={resultUrl} />
          </div>
        )}
      </main>
    </div>
  );
}