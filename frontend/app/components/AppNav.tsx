"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { getCurrentUser, getToken, CurrentUser } from "@/lib/auth";

const NEW_OPTIONS = [
  { label: "Clip a video", href: "/upload" },
  { label: "Generate an image", href: "/generate-image" },
  { label: "Text to speech", href: "/text-to-speech" },
  { label: "Reformat a video", href: "/reformat" },
  { label: "Script to video", href: "/script-to-video" },
];

export default function AppNav() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [newOpen, setNewOpen] = useState(false);

  useEffect(() => {
    if (!getToken()) return;
    getCurrentUser()
      .then(setUser)
      .catch(() => {});
  }, []);

  const initials = user?.full_name
    ? user.full_name.trim().slice(0, 2).toUpperCase()
    : user?.email?.slice(0, 2).toUpperCase() || "?";

  return (
    <header className="sticky top-0 z-40 border-b border-[#1A2434] bg-[#0A0F1A]/90 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between relative">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-[22px] h-[22px] rounded-md bg-[#C9A24B]" />
          <span className="text-[14px] text-[#F4F6F8] font-medium">ClipMind</span>
        </Link>

        <div className="flex items-center gap-3">
          <div className="relative">
            <button
              onClick={() => setNewOpen((v) => !v)}
              className="bg-[#3B7DD8] text-[#F4F6F8] text-[12px] font-medium px-4 py-2 rounded-lg hover:bg-[#4A8AE0] transition flex items-center gap-1.5"
            >
              + New
            </button>
            {newOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setNewOpen(false)} />
                <div className="absolute top-full right-0 mt-2 w-60 bg-[#0F1622] border border-[#22304A] rounded-xl p-1.5 shadow-2xl z-50">
                  {NEW_OPTIONS.map((opt) => (
                    <Link
                      key={opt.href}
                      href={opt.href}
                      className="block px-3 py-2.5 rounded-lg hover:bg-white/5 transition text-[13px] text-[#DCE6F2]"
                    >
                      {opt.label}
                    </Link>
                  ))}
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-1.5 bg-[#141C2C] border border-[#22304A] rounded-full px-3 py-1.5">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="#8FBBF0" stroke="none">
              <path d="M13 2 3 14h7l-1 8 11-14h-7l1-6z" />
            </svg>
            <span className="text-[12px] text-[#DCE6F2] font-mono">
              {user?.credits_remaining ?? "—"}
            </span>
          </div>

          <button
            onClick={() => router.push("/profile")}
            className="w-8 h-8 rounded-full bg-[#3B7DD8] text-[#F4F6F8] text-[12px] font-medium flex items-center justify-center"
          >
            {initials}
          </button>
        </div>
      </div>
    </header>
  );
}