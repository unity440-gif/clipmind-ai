"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

interface Video {
  id: string;
  project_id: string;
  original_filename: string | null;
  file_size_bytes: number | null;
  created_at: string;
}

interface Clip {
  id: string;
  video_id: string;
  start_time_seconds: number;
  end_time_seconds: number;
  title: string | null;
  hook: string | null;
  summary: string | null;
  reason: string | null;
  virality_score: number | null;
  confidence_score: number | null;
  tiktok_caption: string | null;
  instagram_caption: string | null;
  youtube_caption: string | null;
  hashtags: string[] | null;
  status: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [videos, setVideos] = useState<Video[]>([]);
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState("");

  async function loadData() {
    const token = getToken();
    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const projectVideos = await apiFetch(`/projects/${projectId}/videos`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setVideos(projectVideos);

      // For simplicity, we show clips for the first video in the project.
      // (Most projects will only ever have one video.)
      if (projectVideos.length > 0) {
        const videoClips = await apiFetch(`/videos/${projectVideos[0].id}/clips`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setClips(videoClips);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load project.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleDetectHooks() {
    if (videos.length === 0) return;
    setDetecting(true);
    setError("");

    try {
      const token = getToken();
      await apiFetch(`/videos/${videos[0].id}/detect-hooks`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hook detection failed.");
    } finally {
      setDetecting(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-neutral-400">
        Loading...
      </div>
    );
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
        <button
          onClick={handleDetectHooks}
          disabled={detecting || videos.length === 0}
          className="rounded-lg bg-white text-black text-sm font-medium px-4 py-2 hover:bg-neutral-200 transition disabled:opacity-50"
        >
          {detecting ? "Analyzing transcript..." : "Run AI Hook Detection"}
        </button>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold mb-2">Generated Clips</h1>
        <p className="text-neutral-500 text-sm mb-8">
          {clips.length} clip{clips.length !== 1 ? "s" : ""} generated, ranked by predicted virality
        </p>

        {error && (
          <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2 mb-6">
            {error}
          </p>
        )}

        {clips.length === 0 ? (
          <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center text-neutral-500">
            No clips yet. Click &quot;Run AI Hook Detection&quot; above once this video has a transcript.
          </div>
        ) : (
          <div className="space-y-6">
            {clips.map((clip) => (
              <div
                key={clip.id}
                className="rounded-xl border border-neutral-800 bg-neutral-950 p-5"
              >
                <div className="flex items-start justify-between mb-3">
                  <h2 className="text-lg font-medium">{clip.title}</h2>
                  <span className="text-xs px-2 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-400 whitespace-nowrap ml-3">
                    🔥 {clip.virality_score}/100
                  </span>
                </div>

                <p className="text-sm text-neutral-400 mb-4">{clip.summary}</p>

                {clip.status === "completed" ? (
                  <video
                    controls
                    className="w-full rounded-lg mb-4 bg-black"
                    src={`${API_URL}/uploads/clip_${clip.id}.mp4`}
                  />
                ) : (
                  <div className="w-full rounded-lg mb-4 bg-neutral-900 border border-neutral-800 py-8 text-center text-sm text-neutral-500">
                    {clip.status === "failed" ? "Rendering failed" : "Rendering video..."}
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="rounded-lg bg-neutral-900 border border-neutral-800 p-3">
                    <p className="text-neutral-500 mb-1">TikTok</p>
                    <p className="text-neutral-300">{clip.tiktok_caption}</p>
                  </div>
                  <div className="rounded-lg bg-neutral-900 border border-neutral-800 p-3">
                    <p className="text-neutral-500 mb-1">Instagram</p>
                    <p className="text-neutral-300">{clip.instagram_caption}</p>
                  </div>
                  <div className="rounded-lg bg-neutral-900 border border-neutral-800 p-3">
                    <p className="text-neutral-500 mb-1">YouTube</p>
                    <p className="text-neutral-300">{clip.youtube_caption}</p>
                  </div>
                </div>

                {clip.hashtags && (
                  <p className="text-xs text-neutral-500 mt-3">
                    {clip.hashtags.map((tag) => `#${tag}`).join(" ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}