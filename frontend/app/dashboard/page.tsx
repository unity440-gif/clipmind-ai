"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import AppNav from "@/app/components/AppNav";

interface Project {
  id: string;
  title: string;
  status: string;
  created_at: string;
}

const NEW_OPTIONS = [
  { label: "Clip a video", href: "/upload" },
  { label: "Generate an image", href: "/generate-image" },
  { label: "Text to speech", href: "/text-to-speech" },
  { label: "Reformat a video", href: "/reformat" },
  { label: "Script to video", href: "/script-to-video" },
];

export default function DashboardPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [newOpen, setNewOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function loadProjects() {
    const token = getToken();
    const myProjects = await apiFetch("/projects", {
      headers: { Authorization: `Bearer ${token}` },
    });
    setProjects(myProjects);
  }

  useEffect(() => {
    async function load() {
      if (!getToken()) {
        router.push("/login");
        return;
      }
      try {
        await loadProjects();
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function handleDelete(e: React.MouseEvent, projectId: string) {
    e.stopPropagation();
    if (!confirm("Delete this project permanently? This cannot be undone.")) return;

    setDeletingId(projectId);
    try {
      const token = getToken();
      await apiFetch(`/projects/${projectId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      await loadProjects();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Failed to delete project.");
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0F1A] flex items-center justify-center text-[#6E7A8C]">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0F1A] text-white">
      <AppNav />

      <main className="max-w-2xl mx-auto px-6 pt-20 pb-16 text-center">
        <p className="text-[12px] text-[#6E7A8C] mb-3.5 tracking-wide">Welcome back</p>
        <h1 className="text-[25px] text-[#F4F6F8] mb-8 font-normal">
          What do you want to make today?
        </h1>

        <div className="relative inline-block">
          <button
            onClick={() => setNewOpen((v) => !v)}
            className="bg-[#3B7DD8] text-[#F4F6F8] text-[13px] font-medium px-6 py-2.5 rounded-lg hover:bg-[#4A8AE0] transition"
          >
            + New
          </button>
          {newOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setNewOpen(false)} />
              <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 bg-[#0F1622] border border-[#22304A] rounded-xl p-1.5 shadow-2xl z-50 text-left">
                {NEW_OPTIONS.map((opt) => (
                  <button
                    key={opt.href}
                    onClick={() => router.push(opt.href)}
                    className="w-full text-left block px-3 py-2.5 rounded-lg hover:bg-white/5 transition text-[13px] text-[#DCE6F2]"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="mt-14 text-left">
          <p className="text-[11px] text-[#6E7A8C] mb-3.5 tracking-wide">RECENT</p>

          {projects.length === 0 ? (
            <div className="rounded-xl border border-dashed border-[#1A2434] py-16 text-center text-[#6E7A8C] text-[13px]">
              No projects yet. Click &quot;+ New&quot; to get started.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {projects.map((project) => (
                <div
                  key={project.id}
                  onClick={() => router.push(`/projects/${project.id}`)}
                  className="bg-[#0F1622] border border-[#1A2434] rounded-xl p-4 hover:border-[#2A3B52] transition cursor-pointer relative group"
                >
                  <button
                    onClick={(e) => handleDelete(e, project.id)}
                    disabled={deletingId === project.id}
                    className="absolute top-3 right-3 text-[#4A5568] hover:text-[#D98787] transition text-xs opacity-0 group-hover:opacity-100"
                  >
                    {deletingId === project.id ? "…" : "✕"}
                  </button>
                  <p className="text-[13px] text-[#F4F6F8] mb-2 pr-4">{project.title}</p>
                  <span className="inline-block text-[10px] text-[#8FBBF0] bg-[#141F30] px-2 py-1 rounded-full">
                    {project.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}