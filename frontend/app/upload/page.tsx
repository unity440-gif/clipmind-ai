"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const CHUNK_SIZE = 10 * 1024 * 1024; // 10MB per chunk — safely under Railway's timeout

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
    // Step 1: tell the backend we're starting a chunked upload
    const initData = await apiFetch(`/projects/${projectId}/videos/init-upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: JSON.stringify({ filename: file.name, total_size: file.size }),
    });

    const uploadId = initData.upload_id;
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);

    // Step 2: upload each chunk one at a time, in order
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

    // Step 3: tell the backend to reassemble the chunks into the final file
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
        // Always use chunked upload — safe and reliable for any file size,
        // small or large, since each individual request stays small.
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
    <div className="min-h-screen bg-black text-white flex items-center justify-center px-4">
      <div className="w-full max-w-lg">
        <h1 className="text-2xl font-semibold mb-6">Create a new project</h1>

        <div className="flex gap-2 mb-6 bg-neutral-900 border border-neutral-800 rounded-lg p-1">
          <button
            type="button"
            onClick={() => setMode("file")}
            className={`flex-1 rounded-md py-2 text-sm font-medium transition ${
              mode === "file" ? "bg-white text-black" : "text-neutral-400 hover:text-white"
            }`}
          >
            Upload a file
          </button>
          <button
            type="button"
            onClick={() => setMode("youtube")}
            className={`flex-1 rounded-md py-2 text-sm font-medium transition ${
              mode === "youtube" ? "bg-white text-black" : "text-neutral-400 hover:text-white"
            }`}
          >
            Paste YouTube URL
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm text-neutral-400 mb-1">Project title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. My Podcast Episode 12"
              className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
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
                <p className="text-neutral-300">
                  {file.name} ({(file.size / (1024 * 1024)).toFixed(0)} MB)
                </p>
              ) : (
                <>
                  <p className="text-neutral-400">Drag and drop a video here</p>
                  <p className="text-neutral-600 text-sm mt-1">
                    or click to browse — MP4, MOV, AVI, MKV
                  </p>
                </>
              )}
            </div>
          ) : (
            <div>
              <label className="block text-sm text-neutral-400 mb-1">YouTube URL</label>
              <input
                type="url"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
              />
            </div>
          )}

          {uploading && mode === "file" && (
            <div>
              <div className="w-full bg-neutral-900 rounded-full h-2 overflow-hidden mb-1">
                <div
                  className="bg-white h-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-xs text-neutral-500">{statusText}</p>
            </div>
          )}

          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={uploading}
            className="w-full rounded-lg bg-white text-black font-medium py-2.5 hover:bg-neutral-200 transition disabled:opacity-50"
          >
            {uploading
              ? mode === "youtube"
                ? "Downloading from YouTube..."
                : `Uploading... ${progress}%`
              : "Create Project"}
          </button>
        </form>
      </div>
    </div>
  );
}