"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, getToken, CurrentUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const [editing, setEditing] = useState(false);
  const [step, setStep] = useState<"form" | "code">("form");
  const [fullName, setFullName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function loadUser() {
    const currentUser = await getCurrentUser();
    setUser(currentUser);
    setFullName(currentUser.full_name || "");
    setNewEmail(currentUser.email);
  }

  useEffect(() => {
    async function load() {
      if (!getToken()) {
        router.push("/login");
        return;
      }
      try {
        await loadUser();
      } catch {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function handleRequestChange(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const token = getToken();
      const body: { full_name?: string; new_email?: string } = {};
      if (fullName !== user?.full_name) body.full_name = fullName;
      if (newEmail !== user?.email) body.new_email = newEmail;

      if (Object.keys(body).length === 0) {
        setError("Nothing changed.");
        setSubmitting(false);
        return;
      }

      await apiFetch("/auth/profile/request-change", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify(body),
      });
      setStep("code");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleConfirmCode(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      const token = getToken();
      await apiFetch("/auth/profile/confirm-change", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ code }),
      });
      await loadUser();
      setEditing(false);
      setStep("form");
      setCode("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Verification failed.");
    } finally {
      setSubmitting(false);
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
      </header>

      <main className="max-w-lg mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-semibold">Your Profile</h1>
          {!editing && (
            <button
              onClick={() => setEditing(true)}
              className="text-sm text-neutral-400 hover:text-white transition"
            >
              Edit
            </button>
          )}
        </div>

        {!editing ? (
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
        ) : step === "form" ? (
          <form onSubmit={handleRequestChange} className="space-y-4">
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Full name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
              />
            </div>
            <div>
              <label className="block text-sm text-neutral-400 mb-1">Email</label>
              <input
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
              />
            </div>

            {error && (
              <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-white text-black text-sm font-medium px-4 py-2.5 hover:bg-neutral-200 transition disabled:opacity-50"
              >
                {submitting ? "Sending code..." : "Send verification code"}
              </button>
              <button
                type="button"
                onClick={() => setEditing(false)}
                className="text-sm text-neutral-400 hover:text-white transition"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleConfirmCode} className="space-y-4">
            <p className="text-sm text-neutral-400">
              We sent a 6-digit code to your current email ({user?.email}). Enter it below to confirm.
            </p>
            <input
              type="text"
              required
              maxLength={6}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="000000"
              className="w-full text-center text-2xl tracking-[0.5em] rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-3 outline-none focus:border-neutral-600"
            />

            {error && (
              <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
                {error}
              </p>
            )}

            <div className="flex gap-3">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-lg bg-white text-black text-sm font-medium px-4 py-2.5 hover:bg-neutral-200 transition disabled:opacity-50"
              >
                {submitting ? "Verifying..." : "Confirm change"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setEditing(false);
                  setStep("form");
                }}
                className="text-sm text-neutral-400 hover:text-white transition"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}