"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

interface Scene {
  id: string;
  scene_number: number;
  description: string;
  narration_text: string;
  image_url: string | null;
  audio_url: string | null;
  status: string;
}

interface ScriptProjectData {
  id: string;
  title: string;
  status: string;
  compiled_video_url: string | null;
  scenes: Scene[];
}

export default function ScriptToVideoPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [scriptText, setScriptText] = useState("");
  const [project, setProject] = useState<ScriptProjectData | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [compiling, setCompiling] = useState(false);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const token = getToken();
      const data = await apiFetch("/scripts", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title, script_text: scriptText }),
      });
      setProject(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit script.");
    } finally {
      setSubmitting(false);
    }
  }

  async function pollStatus(projectId: string) {
    const token = getToken();
    const data = await apiFetch(`/scripts/${projectId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    setProject(data);

    if (data.status === "scenes_ready" || data.status === "completed" || data.status === "failed") {
      if (pollRef.current) clearInterval(pollRef.current);
    }
  }

  useEffect(() => {
    if (project && !["scenes_ready", "completed", "failed"].includes(project.status)) {
      pollRef.current = setInterval(() => pollStatus(project.id), 4000);
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [project?.id, project?.status]);

  async function handleCompile() {
    if (!project) return;
    setCompiling(true);
    setError("");

    try {
      const token = getToken();
      await apiFetch(`/scripts/${project.id}/compile`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      pollRef.current = setInterval(() => pollStatus(project.id), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compilation failed to start.");
    } finally {
      setCompiling(false);
    }
  }

  const statusLabels: Record<string, string> = {
    pending: "Starting...",
    breaking_down_script: "Breaking script into scenes...",
    generating_scenes: "Generating images and narration...",
    scenes_ready: "Scenes ready!",
    compiling_video: "Compiling final video (this can take a few minutes)...",
    completed: "Video ready!",
    failed: "Something went wrong.",
  };

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="border-b border-neutral-800 px-6 py-4 flex items-center justify-between">
        <button onClick={() => router.push("/dashboard")} className="text-sm text-neutral-400 hover:text-white transition">
          ← Back to Dashboard
        </button>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold mb-2">Script to Video</h1>
        <p className="text-neutral-500 text-sm mb-8">
          Paste a script, AI breaks it into scenes, generates an image and narration for each, and compiles it into a video. Costs 1 credit per scene.
        </p>

        {!project ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Title</label>
              <input type="text" required value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600" />
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Script</label>
              <textarea required rows={8} value={scriptText} onChange={(e) => setScriptText(e.target.value)} placeholder="Paste your story or script here..." className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600 resize-none" />
            </div>

            {error ? (
              <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">{error}</p>
            ) : null}

            <button type="submit" disabled={submitting} className="rounded-lg bg-white text-black text-sm font-medium px-5 py-2.5 hover:bg-neutral-200 transition disabled:opacity-50">
              {submitting ? "Submitting..." : "Generate Scenes"}
            </button>
          </form>
        ) : (
          <div>
            <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 mb-6">
              <p className="text-sm text-neutral-400">{statusLabels[project.status] || project.status}</p>
            </div>

            {project.status === "scenes_ready" ? (
              <button onClick={handleCompile} disabled={compiling} className="rounded-lg bg-white text-black text-sm font-medium px-5 py-2.5 hover:bg-neutral-200 transition disabled:opacity-50 mb-6">
                {compiling ? "Starting..." : "Compile into Video"}
              </button>
            ) : null}

            {project.status === "completed" && project.compiled_video_url ? (
              <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5 mb-8">
                <video controls className="w-full rounded-lg mb-4" src={project.compiled_video_url} />
                <a href={project.compiled_video_url} download={project.title + ".mp4"} className="inline-block rounded-lg bg-white text-black text-sm font-medium px-5 py-2.5 hover:bg-neutral-200 transition">
                  Download Video
                </a>
              </div>
            ) : null}

            <div className="space-y-4">
              {project.scenes.map((scene) => (
                <div key={scene.id} className="rounded-xl border border-neutral-800 bg-neutral-950 p-4">
                  <p className="text-xs text-neutral-600 mb-2">Scene {scene.scene_number}</p>
                  <p className="text-sm text-neutral-300 mb-3">{scene.narration_text}</p>
                  {scene.image_url ? (
                    <img src={scene.image_url} alt={scene.description} className="rounded-lg max-w-sm" />
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
