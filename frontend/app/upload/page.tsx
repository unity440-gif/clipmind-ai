"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
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

    if (!file) {
      setError("Please choose a video file.");
      return;
    }

    setUploading(true);
    setProgress(0);

    try {
      const token = getToken();

      // Step 1: create the project
      const project = await apiFetch("/projects", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title }),
      });

      // Step 2: upload the video into it.
      // We use raw XMLHttpRequest here (not fetch) specifically because
      // fetch has no built-in way to report upload progress — XHR does.
      await new Promise<void>((resolve, reject) => {
        const formData = new FormData();
        formData.append("file", file);

        const xhr = new XMLHttpRequest();
        xhr.open("POST", `${API_URL}/projects/${project.id}/videos`);
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);

        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            setProgress(Math.round((event.loaded / event.total) * 100));
          }
        };

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new Error("Upload failed."));
          }
        };
        xhr.onerror = () => reject(new Error("Upload failed."));

        xhr.send(formData);
      });

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
        <h1 className="text-2xl font-semibold mb-6">Upload a video</h1>

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
              <>
                <p className="text-neutral-400">Drag and drop a video here</p>
                <p className="text-neutral-600 text-sm mt-1">
                  or click to browse — MP4, MOV, AVI, MKV
                </p>
              </>
            )}
          </div>

          {uploading && (
            <div className="w-full bg-neutral-900 rounded-full h-2 overflow-hidden">
              <div
                className="bg-white h-full transition-all"
                style={{ width: `${progress}%` }}
              />
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
            {uploading ? `Uploading... ${progress}%` : "Upload"}
          </button>
        </form>
      </div>
    </div>
  );
}