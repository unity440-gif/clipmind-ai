"use client";

import { useState, useRef } from "react";
import { getToken } from "@/lib/auth";
import AppNav from "@/app/components/AppNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function ReformatPage() {
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
    <div className="min-h-screen bg-[#0A0F1A] text-white">
      <AppNav />

      <main className="max-w-[480px] mx-auto px-6 pt-16 pb-16">
        <p className="text-[19px] text-[#F4F6F8] mb-1">Quick reformat</p>
        <p className="text-[12px] text-[#6E7A8C] mb-8">
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
            className={`rounded-xl border-[1.5px] border-dashed px-6 py-11 text-center cursor-pointer transition ${
              dragActive ? "border-[#3B7DD8] bg-[#0F1622]" : "border-[#22304A] hover:border-[#2A3B52]"
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
              <p className="text-[13px] text-[#DCE6F2]">{file.name}</p>
            ) : (
              <p className="text-[13px] text-[#9AA7B8]">Drag and drop a video, or click to browse</p>
            )}
          </div>

          <div>
            <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Target aspect ratio</label>
            <div className="flex gap-2">
              {["9:16", "16:9", "1:1"].map((ratio) => (
                <button
                  key={ratio}
                  type="button"
                  onClick={() => setAspectRatio(ratio)}
                  className={`text-[12px] px-3.5 py-1.5 rounded-lg border transition ${
                    aspectRatio === ratio
                      ? "bg-[#141F30] text-[#8FBBF0] border-[#3B7DD8]"
                      : "text-[#9AA7B8] border-[#22304A] hover:border-[#2A3B52]"
                  }`}
                >
                  {ratio}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p className="text-[13px] text-[#D98787] bg-[#2A1616]/60 border border-[#4A2222] rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-[#3B7DD8] text-white text-[13px] font-medium px-5 py-2.5 hover:bg-[#4A8AE0] transition disabled:opacity-50 w-full"
          >
            {loading ? "Processing... (this can take a bit for longer videos)" : "Reformat video"}
          </button>
        </form>

        {resultUrl && (
          <div className="mt-8 rounded-xl border border-[#1A2434] bg-[#0F1622] p-4">
            <video controls className="w-full rounded-lg" src={resultUrl} />
          </div>
        )}
      </main>
    </div>
  );
}