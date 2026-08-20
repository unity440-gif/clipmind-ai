"use client";

import { useState, useEffect, useRef } from "react";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import AppNav from "@/app/components/AppNav";

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
    <div className="min-h-screen bg-[#0A0F1A] text-white">
      <AppNav />

      <main className="max-w-[560px] mx-auto px-6 pt-16 pb-16">
        <p className="text-[19px] text-[#F4F6F8] mb-1">Script to video</p>
        <p className="text-[12px] text-[#6E7A8C] mb-8">
          AI breaks it into scenes, generates an image and narration for each, and compiles it into a video. Costs 1 credit per scene.
        </p>

        {!project ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Title</label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[14px] px-3.5 py-2.5 outline-none focus:border-[#3B7DD8] transition"
              />
            </div>
            <div>
              <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Script</label>
              <textarea
                required
                rows={8}
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                placeholder="Paste your story or script here..."
                className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[14px] px-3.5 py-2.5 outline-none focus:border-[#3B7DD8] transition resize-none"
              />
            </div>

            {error && (
              <p className="text-[13px] text-[#D98787] bg-[#2A1616]/60 border border-[#4A2222] rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-[#3B7DD8] text-white text-[13px] font-medium px-5 py-2.5 hover:bg-[#4A8AE0] transition disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Generate scenes"}
            </button>
          </form>
        ) : (
          <div>
            <div className="rounded-xl border border-[#1A2434] bg-[#0F1622] p-4 mb-6">
              <p className="text-[13px] text-[#DCE6F2]">{statusLabels[project.status] || project.status}</p>
            </div>

            {project.status === "scenes_ready" && (
              <button
                onClick={handleCompile}
                disabled={compiling}
                className="rounded-lg bg-[#3B7DD8] text-white text-[13px] font-medium px-5 py-2.5 hover:bg-[#4A8AE0] transition disabled:opacity-50 mb-6"
              >
                {compiling ? "Starting..." : "Compile into video"}
              </button>
            )}

            {project.status === "completed" && project.compiled_video_url ? (
              <div className="rounded-xl border border-[#1A2434] bg-[#0F1622] p-4 mb-8">
                <video controls className="w-full rounded-lg mb-3" src={project.compiled_video_url} />
                
                  href={project.compiled_video_url}
                  download={`${project.title}.mp4`}
                  className="inline-block rounded-lg bg-[#3B7DD8] text-white text-[12px] font-medium px-4 py-2 hover:bg-[#4A8AE0] transition"
                >
                  Download video
                </a>
              </div>
            ) : null}

            <p className="text-[11px] text-[#6E7A8C] mb-3">SCENES</p>
            <div className="grid grid-cols-2 gap-3">
              {project.scenes.map((scene) => (
                <div key={scene.id} className="rounded-lg bg-[#0F1622] border border-[#1A2434] p-3">
                  <p className="text-[10px] text-[#6E7A8C] mb-2">Scene {scene.scene_number}</p>
                  {scene.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={scene.image_url} alt={scene.description} className="rounded-md mb-2 w-full" />
                  ) : (
                    <div className="rounded-md mb-2 bg-[#141C2C] h-20 flex items-center justify-center">
                      <span className="text-[10px] text-[#4A5568]">Generating...</span>
                    </div>
                  )}
                  <p className="text-[11px] text-[#B8C2D0] leading-[1.4]">{scene.narration_text}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}