"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import AppNav from "@/app/components/AppNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const CHUNK_SIZE = 10 * 1024 * 1024;

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [mode, setMode] = useState<"file" | "youtube">("file");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState("");

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragActive(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) setFile(dropped);
  }

  async function uploadInChunks(projectId: string, file: File, token: string | null) {
    const initData = await apiFetch(`/projects/${projectId}/videos/init-upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ filename: file.name, total_size: file.size }),
    });

    const uploadId = initData.upload_id;
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

    for (let i = 0; i < totalChunks; i++) {
      const start = i * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file.size);
      const chunkBlob = file.slice(start, end);

      const formData = new FormData();
      formData.append("upload_id", uploadId);
      formData.append("chunk_index", String(i));
      formData.append("file", chunkBlob);

      const response = await fetch(`${API_URL}/projects/${projectId}/videos/upload-chunk`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Chunk ${i + 1} of ${totalChunks} failed to upload.`);
      }

      setProgress(Math.round(((i + 1) / totalChunks) * 100));
      setStatusText(`Uploading chunk ${i + 1} of ${totalChunks}...`);
    }

    setStatusText("Finalizing upload...");
    await apiFetch(`/projects/${projectId}/videos/complete-upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ upload_id: uploadId, filename: file.name }),
    });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (mode === "file" && !file) {
      setError("Please choose a video file.");
      return;
    }
    if (mode === "youtube" && !youtubeUrl.trim()) {
      setError("Please paste a YouTube URL.");
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      const token = getToken();

      const project = await apiFetch("/projects", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title }),
      });

      if (mode === "youtube") {
        const params = new URLSearchParams({ youtube_url: youtubeUrl.trim() });
        await apiFetch(`/projects/${project.id}/videos/from-youtube?${params.toString()}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await uploadInChunks(project.id, file as File, token);
      }

      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0F1A] text-white">
      <AppNav />

      <main className="max-w-[480px] mx-auto px-6 pt-16 pb-16">
        <p className="text-[19px] text-[#F4F6F8] mb-1">Clip a video</p>
        <p className="text-[12px] text-[#6E7A8C] mb-8">
          Upload a file or paste a YouTube link to get started.
        </p>

        <div className="flex gap-1 mb-6 bg-[#0F1622] border border-[#1A2434] rounded-lg p-1">
          <button
            type="button"
            onClick={() => setMode("file")}
            className={`flex-1 rounded-md py-2 text-[13px] font-medium transition ${
              mode === "file" ? "bg-[#3B7DD8] text-white" : "text-[#6E7A8C] hover:text-[#DCE6F2]"
            }`}
          >
            Upload a file
          </button>
          <button
            type="button"
            onClick={() => setMode("youtube")}
            className={`flex-1 rounded-md py-2 text-[13px] font-medium transition ${
              mode === "youtube" ? "bg-[#3B7DD8] text-white" : "text-[#6E7A8C] hover:text-[#DCE6F2]"
            }`}
          >
            Paste YouTube URL
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Project title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. My Podcast Episode 12"
              className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[14px] px-3.5 py-2.5 outline-none focus:border-[#3B7DD8] transition"
            />
          </div>

          {mode === "file" ? (
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
                <p className="text-[13px] text-[#DCE6F2]">
                  {file.name} ({(file.size / (1024 * 1024)).toFixed(0)} MB)
                </p>
              ) : (
                <>
                  <p className="text-[13px] text-[#9AA7B8] mb-1">Drag and drop a video here</p>
                  <p className="text-[11px] text-[#5C6577]">or click to browse — MP4, MOV, AVI, MKV</p>
                </>
              )}
            </div>
          ) : (
            <div>
              <label className="block text-[12px] text-[#9AA7B8] mb-1.5">YouTube URL</label>
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[14px] px-3.5 py-2.5 outline-none focus:border-[#3B7DD8] transition"
              />
            </div>
          )}

          {uploading && mode === "file" && (
            <div>
              <div className="w-full bg-[#0F1622] rounded-full h-1.5 overflow-hidden mb-1.5">
                <div className="bg-[#3B7DD8] h-full transition-all" style={{ width: `${progress}%` }} />
              </div>
              <p className="text-[11px] text-[#6E7A8C]">{statusText}</p>
            </div>
          )}

          {error && (
            <p className="text-[13px] text-[#D98787] bg-[#2A1616]/60 border border-[#4A2222] rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={uploading}
            className="w-full rounded-lg bg-[#3B7DD8] text-white text-[13px] font-medium py-2.5 hover:bg-[#4A8AE0] transition disabled:opacity-50"
          >
            {uploading
              ? mode === "youtube"
                ? "Downloading from YouTube..."
                : `Uploading... ${progress}%`
              : "Create Project"}
          </button>
        </form>
      </main>
    </div>
  );
}