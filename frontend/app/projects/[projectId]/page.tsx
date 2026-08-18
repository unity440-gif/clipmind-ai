"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

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

interface CaptionEntry {
  index: number;
  start: number;
  end: number;
  text: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.projectId as string;

  const [videos, setVideos] = useState<Video[]>([]);
  const [clips, setClips] = useState<Clip[]>([]);
  const [clipUrls, setClipUrls] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState("");

  const [minDuration, setMinDuration] = useState(60);
  const [maxDuration, setMaxDuration] = useState(120);
  const [aspectRatio, setAspectRatio] = useState("original");
  const [numClips, setNumClips] = useState(5);
  const [burnCaptions, setBurnCaptions] = useState(true);

  const [editingClipId, setEditingClipId] = useState<string | null>(null);
  const [captions, setCaptions] = useState<CaptionEntry[]>([]);
  const [captionsLoading, setCaptionsLoading] = useState(false);
  const [savingCaptions, setSavingCaptions] = useState(false);
  const [captionError, setCaptionError] = useState("");

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

      if (projectVideos.length > 0) {
        const videoClips = await apiFetch(`/videos/${projectVideos[0].id}/clips`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setClips(videoClips);

        const urls: Record<string, string> = {};
        await Promise.all(
          videoClips
            .filter((c: Clip) => c.status === "completed")
            .map(async (c: Clip) => {
              try {
                const data = await apiFetch(`/videos/clip-url/${c.id}`, {
                  headers: { Authorization: `Bearer ${token}` },
                });
                urls[c.id] = data.url;
              } catch {
                // skip silently if one clip's URL fails
              }
            })
        );
        setClipUrls(urls);
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
        body: JSON.stringify({
          min_duration: minDuration,
          max_duration: maxDuration,
          aspect_ratio: aspectRatio,
          num_clips: numClips,
          burn_captions: burnCaptions,
        }),
      });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Hook detection failed.");
    } finally {
      setDetecting(false);
    }
  }

  async function openCaptionEditor(clipId: string) {
    setEditingClipId(clipId);
    setCaptionError("");
    setCaptionsLoading(true);
    try {
      const token = getToken();
      const data = await apiFetch(`/videos/clips/${clipId}/captions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCaptions(data.captions);
    } catch (err) {
      setCaptionError(err instanceof Error ? err.message : "Failed to load captions.");
    } finally {
      setCaptionsLoading(false);
    }
  }

  function updateCaptionText(index: number, newText: string) {
    setCaptions((prev) =>
      prev.map((c) => (c.index === index ? { ...c, text: newText } : c))
    );
  }

  async function handleSaveCaptions() {
    if (!editingClipId) return;
    setSavingCaptions(true);
    setCaptionError("");

    try {
      const token = getToken();
      await apiFetch(`/videos/clips/${editingClipId}/captions`, {
        method: "PUT",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ captions }),
      });
      setEditingClipId(null);
      await loadData();
    } catch (err) {
      setCaptionError(err instanceof Error ? err.message : "Failed to save captions.");
    } finally {
      setSavingCaptions(false);
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
        <button onClick={() => router.push("/dashboard")} className="text-sm text-neutral-400 hover:text-white transition">
          ← Back to Dashboard
        </button>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold mb-2">Generated Clips</h1>
        <p className="text-neutral-500 text-sm mb-6">
          {clips.length} clip{clips.length !== 1 ? "s" : ""} generated, ranked by predicted virality
        </p>

        <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 mb-8">
          <h2 className="text-sm font-medium mb-4 text-neutral-300">Clip Settings</h2>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Min length (sec)</label>
              <input type="number" min={5} max={300} value={minDuration} onChange={(e) => setMinDuration(Number(e.target.value))} className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-3 py-2 text-sm outline-none focus:border-neutral-600" />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Max length (sec)</label>
              <input type="number" min={5} max={300} value={maxDuration} onChange={(e) => setMaxDuration(Number(e.target.value))} className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-3 py-2 text-sm outline-none focus:border-neutral-600" />
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1">Aspect ratio</label>
              <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)} className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-3 py-2 text-sm outline-none focus:border-neutral-600">
                <option value="original">Original</option>
                <option value="16:9">16:9 (Landscape)</option>
                <option value="9:16">9:16 (Vertical)</option>
                <option value="1:1">1:1 (Square)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-neutral-500 mb-1"># of clips</label>
              <input type="number" min={1} max={10} value={numClips} onChange={(e) => setNumClips(Number(e.target.value))} className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-3 py-2 text-sm outline-none focus:border-neutral-600" />
            </div>
          </div>

          <label className="flex items-center gap-2 text-sm text-neutral-400 cursor-pointer mb-4">
            <input type="checkbox" checked={burnCaptions} onChange={(e) => setBurnCaptions(e.target.checked)} className="w-4 h-4" />
            Burn captions into clips
          </label>

          <button onClick={handleDetectHooks} disabled={detecting || videos.length === 0} className="rounded-lg bg-white text-black text-sm font-medium px-4 py-2 hover:bg-neutral-200 transition disabled:opacity-50">
            {detecting ? "Analyzing transcript..." : "Run AI Hook Detection (1 credit)"}
          </button>
        </div>

        {error ? (
          <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2 mb-6">{error}</p>
        ) : null}

        {clips.length === 0 ? (
          <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center text-neutral-500">
            No clips yet. Adjust settings above and click &quot;Run AI Hook Detection&quot;.
          </div>
        ) : (
          <div className="space-y-6">
            {clips.map((clip) => (
              <div key={clip.id} className="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
                <div className="flex items-start justify-between mb-3">
                  <h2 className="text-lg font-medium">{clip.title}</h2>
                  <span className="text-xs px-2 py-1 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-400 whitespace-nowrap ml-3">
                    🔥 {clip.virality_score}/100
                  </span>
                </div>

                <p className="text-sm text-neutral-400 mb-4">{clip.summary}</p>

                {clip.status === "completed" && clipUrls[clip.id] ? (<div className="mb-4"><video controls className="w-full rounded-lg mb-2 bg-black" src={clipUrls[clip.id]} /><a href={clipUrls[clip.id]} download={`${clip.title || "clip"}.mp4`} className="inline-block text-xs rounded-lg bg-neutral-800 text-white px-3 py-1.5 hover:bg-neutral-700 transition">Download Clip</a></div>) : (
                  <div className="w-full rounded-lg mb-4 bg-neutral-900 border border-neutral-800 py-8 text-center text-sm text-neutral-500">
                    {clip.status === "failed" ? "Rendering failed" : "Rendering video..."}
                  </div>
                )}

                {clip.status === "completed" ? (
                  <button onClick={() => openCaptionEditor(clip.id)} className="text-xs text-neutral-400 hover:text-white transition mb-4 underline">
                    Edit captions
                  </button>
                ) : null}

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

                {clip.hashtags ? (
                  <p className="text-xs text-neutral-500 mt-3">
                    {clip.hashtags.map((tag) => `#${tag}`).join(" ")}
                  </p>
                ) : null}
              </div>
            ))}
          </div>
        )}
      </main>

      {editingClipId ? (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center px-4 z-50">
          <div className="bg-neutral-950 border border-neutral-800 rounded-xl w-full max-w-lg max-h-[80vh] flex flex-col">
            <div className="p-5 border-b border-neutral-800 flex items-center justify-between">
              <h3 className="font-medium">Edit Captions</h3>
              <button onClick={() => setEditingClipId(null)} className="text-neutral-500 hover:text-white transition">✕</button>
            </div>

            <div className="p-5 overflow-y-auto flex-1 space-y-3">
              {captionsLoading ? (
                <p className="text-sm text-neutral-500">Loading captions...</p>
              ) : captionError ? (
                <p className="text-sm text-red-400">{captionError}</p>
              ) : (
                captions.map((c) => (
                  <div key={c.index}>
                    <p className="text-xs text-neutral-600 mb-1">{c.start.toFixed(1)}s – {c.end.toFixed(1)}s</p>
                    <input type="text" value={c.text} onChange={(e) => updateCaptionText(c.index, e.target.value)} className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-3 py-2 text-sm outline-none focus:border-neutral-600" />
                  </div>
                ))
              )}
            </div>

            <div className="p-5 border-t border-neutral-800 flex gap-3">
              <button onClick={handleSaveCaptions} disabled={savingCaptions || captionsLoading} className="rounded-lg bg-white text-black text-sm font-medium px-4 py-2 hover:bg-neutral-200 transition disabled:opacity-50">
                {savingCaptions ? "Saving & re-rendering..." : "Save & Re-render"}
              </button>
              <button onClick={() => setEditingClipId(null)} className="text-sm text-neutral-400 hover:text-white transition">
                Cancel
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}