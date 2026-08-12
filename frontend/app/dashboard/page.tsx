"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, getToken, logout, CurrentUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

interface Project {
  id: string;
  title: string;
  status: string;
  created_at: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
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
        const currentUser = await getCurrentUser();
        setUser(currentUser);
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

    if (!confirm("Delete this project permanently? This cannot be undone.")) {
      return;
    }

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
      <div className="min-h-screen bg-black flex items-center justify-center text-neutral-400">
        Loading...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <header className="border-b border-neutral-800 px-6 py-4 flex items-center justify-between">
        <h1 className="text-lg font-semibold">ClipMind AI</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-neutral-400">
            {user?.credits_remaining} credits
          </span>
          <button
            onClick={() => router.push("/profile")}
            className="text-sm text-neutral-400 hover:text-white transition"
          >
            {user?.email}
          </button>
          <button
            onClick={logout}
            className="text-sm text-neutral-400 hover:text-white transition"
          >
            Log out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Your Projects</h2>
          <div>
            <button
              onClick={() => router.push("/upload")}
              className="rounded-lg bg-white text-black text-sm font-medium px-4 py-2 hover:bg-neutral-200 transition"
            >
              {"+ New Project"}
            </button>
            <button
              onClick={() => router.push("/generate-image")}
              className="rounded-lg bg-neutral-800 text-white text-sm font-medium px-4 py-2 hover:bg-neutral-700 transition ml-2"
            >
              Generate Image
            </button>
            <button
              onClick={() => router.push("/text-to-speech")}
              className="rounded-lg bg-neutral-800 text-white text-sm font-medium px-4 py-2 hover:bg-neutral-700 transition ml-2"
            >
              Text to Speech
            </button>
          </div>
        </div>

        {projects.length === 0 ? (
          <div className="rounded-xl border border-dashed border-neutral-800 py-16 text-center text-neutral-500">
            No projects yet. Upload a video to get started.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => router.push(`/projects/${project.id}`)}
                className="rounded-xl border border-neutral-800 bg-neutral-950 p-4 hover:border-neutral-700 transition cursor-pointer relative group"
              >
                <button
                  onClick={(e) => handleDelete(e, project.id)}
                  disabled={deletingId === project.id}
                  className="absolute top-3 right-3 text-neutral-600 hover:text-red-400 transition text-xs opacity-0 group-hover:opacity-100 disabled:opacity-50"
                  title="Delete project"
                >
                  {deletingId === project.id ? "..." : "✕"}
                </button>
                <h3 className="font-medium mb-1 pr-4">{project.title}</h3>
                <span className="inline-block text-xs px-2 py-1 rounded-full bg-neutral-900 text-neutral-400 border border-neutral-800">
                  {project.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}