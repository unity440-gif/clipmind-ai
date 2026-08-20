"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getCurrentUser, getToken, logout, CurrentUser } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import AppNav from "@/app/components/AppNav";

type Tab = "profile" | "history" | "billing" | "settings";

interface HistoryEntry {
  id: string;
  media_type: string;
  prompt_or_text: string;
  voice: string | null;
  url: string;
  created_at: string;
}

export default function AccountPage() {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("profile");
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

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

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const token = getToken();
      const data = await apiFetch("/history", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory(data);
    } catch {
      // ignore
    } finally {
      setHistoryLoading(false);
    }
  }

  function switchTab(t: Tab) {
    setTab(t);
    if (t === "history" && history.length === 0) loadHistory();
  }

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
      <div className="min-h-screen bg-[#0A0F1A] flex items-center justify-center text-[#6E7A8C]">
        Loading...
      </div>
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: "profile", label: "Profile" },
    { id: "history", label: "History" },
    { id: "billing", label: "Billing" },
    { id: "settings", label: "Settings" },
  ];

  return (
    <div className="min-h-screen bg-[#0A0F1A] text-white">
      <AppNav />

      <div className="border-b border-[#1A2434] px-6">
        <div className="max-w-2xl mx-auto flex gap-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => switchTab(t.id)}
              className={`text-[13px] pb-3.5 pt-4 border-b-2 transition ${
                tab === t.id
                  ? "text-[#F4F6F8] border-[#3B7DD8]"
                  : "text-[#6E7A8C] border-transparent hover:text-[#DCE6F2]"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <main className="max-w-2xl mx-auto px-6 py-8">
        {tab === "profile" && (
          <div className="max-w-[420px]">
            {!editing ? (
              <>
                <div className="border-t border-[#1A2434]">
                  <div className="flex justify-between py-3.5 border-b border-[#1A2434]">
                    <span className="text-[12px] text-[#6E7A8C]">Full name</span>
                    <span className="text-[12px] text-[#F4F6F8]">{user?.full_name || "—"}</span>
                  </div>
                  <div className="flex justify-between py-3.5 border-b border-[#1A2434]">
                    <span className="text-[12px] text-[#6E7A8C]">Email</span>
                    <span className="text-[12px] text-[#F4F6F8]">{user?.email}</span>
                  </div>
                  <div className="flex justify-between py-3.5">
                    <span className="text-[12px] text-[#6E7A8C]">Credits</span>
                    <span className="text-[12px] text-[#F4F6F8]">{user?.credits_remaining}</span>
                  </div>
                </div>
                <button
                  onClick={() => setEditing(true)}
                  className="mt-5 text-[12px] text-[#DCE6F2] border border-[#22304A] px-4 py-2 rounded-lg hover:bg-white/5 transition"
                >
                  Edit profile
                </button>
              </>
            ) : step === "form" ? (
              <form onSubmit={handleRequestChange} className="space-y-4">
                <div>
                  <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Full name</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[13px] px-3 py-2.5 outline-none focus:border-[#3B7DD8] transition"
                  />
                </div>
                <div>
                  <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Email</label>
                  <input
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[13px] px-3 py-2.5 outline-none focus:border-[#3B7DD8] transition"
                  />
                </div>
                {error && <p className="text-[12px] text-[#D98787]">{error}</p>}
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="bg-[#3B7DD8] text-white text-[12px] font-medium px-4 py-2 rounded-lg hover:bg-[#4A8AE0] transition disabled:opacity-50"
                  >
                    {submitting ? "Sending code..." : "Send verification code"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditing(false)}
                    className="text-[12px] text-[#6E7A8C] hover:text-[#DCE6F2] transition"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleConfirmCode} className="space-y-4">
                <p className="text-[12px] text-[#9AA7B8]">
                  Code sent to your current email ({user?.email}).
                </p>
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="000000"
                  className="w-full text-center text-[20px] tracking-[0.4em] rounded-lg bg-[#0F1622] border border-[#22304A] text-white px-4 py-2.5 outline-none focus:border-[#3B7DD8] transition"
                />
                {error && <p className="text-[12px] text-[#D98787]">{error}</p>}
                <div className="flex gap-3">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="bg-[#3B7DD8] text-white text-[12px] font-medium px-4 py-2 rounded-lg hover:bg-[#4A8AE0] transition disabled:opacity-50"
                  >
                    {submitting ? "Verifying..." : "Confirm change"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setEditing(false);
                      setStep("form");
                    }}
                    className="text-[12px] text-[#6E7A8C] hover:text-[#DCE6F2] transition"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </div>
        )}

        {tab === "history" && (
          <div className="max-w-[560px]">
            {historyLoading ? (
              <p className="text-[12px] text-[#6E7A8C]">Loading...</p>
            ) : history.length === 0 ? (
              <p className="text-[12px] text-[#6E7A8C]">No history yet.</p>
            ) : (
              history.map((entry) => (
                <div key={entry.id} className="border-b border-[#1A2434] py-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] text-[#6E7A8C] bg-[#141C2C] px-2 py-0.5 rounded-full capitalize">
                      {entry.media_type}
                      {entry.voice ? ` · ${entry.voice}` : ""}
                    </span>
                    <span className="text-[10px] text-[#4A5568]">
                      {new Date(entry.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-[13px] text-[#DCE6F2] mb-2">{entry.prompt_or_text}</p>
                  {entry.media_type === "image" ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={entry.url} alt="" className="rounded-lg max-w-[200px]" />
                  ) : (
                    <audio controls className="w-full h-8" src={entry.url} />
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {tab === "billing" && (
          <div className="max-w-[560px]">
            <div className="bg-[#0F1622] border border-[#1A2434] rounded-xl p-5 mb-6 flex justify-between">
              <div>
                <p className="text-[11px] text-[#6E7A8C] mb-1.5">Credits remaining</p>
                <p className="text-[26px] text-[#F4F6F8] font-mono">{user?.credits_remaining}</p>
              </div>
              <div className="text-right">
                <p className="text-[11px] text-[#6E7A8C] mb-1.5">Plan</p>
                <p className="text-[13px] text-[#DCE6F2]">Pay as you go</p>
              </div>
            </div>

            <p className="text-[12px] text-[#6E7A8C] mb-2.5">Buy more credits</p>
            <div className="grid grid-cols-3 gap-2.5 mb-8">
              {[
                { credits: 100, price: "$5" },
                { credits: 500, price: "$20", featured: true },
                { credits: 1200, price: "$40" },
              ].map((pkg) => (
                <div
                  key={pkg.credits}
                  className={`rounded-lg p-3.5 text-center border ${
                    pkg.featured ? "border-[#3B7DD8] border-[1.5px]" : "border-[#1A2434]"
                  }`}
                >
                  <p className="text-[16px] text-[#F4F6F8] font-mono">{pkg.credits.toLocaleString()}</p>
                  <p className="text-[10px] text-[#6E7A8C] mb-2.5">credits</p>
                  <button
                    className={`w-full text-[11px] py-1.5 rounded-md ${
                      pkg.featured ? "bg-[#3B7DD8] text-white" : "border border-[#22304A] text-[#DCE6F2]"
                    }`}
                  >
                    {pkg.price}
                  </button>
                </div>
              ))}
            </div>

            <p className="text-[12px] text-[#6E7A8C] mb-2">Recent usage</p>
            <p className="text-[11px] text-[#4A5568]">
              Detailed transaction history coming soon — for now, check your credit balance above.
            </p>
          </div>
        )}

        {tab === "settings" && (
          <div className="max-w-[420px] border-t border-[#1A2434]">
            <div className="flex items-center justify-between py-4 border-b border-[#1A2434]">
              <span className="text-[13px] text-[#DCE6F2]">Signed in as</span>
              <span className="text-[12px] text-[#6E7A8C]">{user?.email}</span>
            </div>
            <button
              onClick={logout}
              className="w-full text-left py-4 text-[13px] text-[#D98787] hover:text-[#E09999] transition"
            >
              Log out
            </button>
          </div>
        )}
      </main>
    </div>
  );
}