"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, getToken, CurrentUser } from "@/lib/auth";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!getToken()) {
        router.push("/login");
        return;
      }
      try {
        const currentUser = await getCurrentUser();
        setUser(currentUser);
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

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
      </header>

      <main className="max-w-lg mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold mb-8">Your Profile</h1>

        <div className="rounded-xl border border-neutral-800 bg-neutral-950 divide-y divide-neutral-800">
          <div className="p-4 flex items-center justify-between">
            <span className="text-sm text-neutral-500">Full name</span>
            <span className="text-sm">{user?.full_name || "—"}</span>
          </div>
          <div className="p-4 flex items-center justify-between">
            <span className="text-sm text-neutral-500">Email</span>
            <span className="text-sm">{user?.email}</span>
          </div>
          <div className="p-4 flex items-center justify-between">
            <span className="text-sm text-neutral-500">Credits remaining</span>
            <span className="text-sm">{user?.credits_remaining}</span>
          </div>
        </div>

        <p className="text-xs text-neutral-600 mt-4">
          To change your name or email, you&apos;ll need to verify it&apos;s really you first.
        </p>
      </main>
    </div>
  );
}