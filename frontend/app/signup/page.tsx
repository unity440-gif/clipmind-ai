"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

declare global {
  interface Window {
    google: any;
  }
}

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const googleButtonRef = useRef<HTMLDivElement>(null);

  async function handleGoogleResponse(response: { credential: string }) {
    setError("");
    setLoading(true);
    try {
      const data = await apiFetch("/auth/google", {
        method: "POST",
        body: JSON.stringify({ credential: response.credential }),
      });
      localStorage.setItem("access_token", data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-up failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const interval = setInterval(() => {
      if (window.google && googleButtonRef.current) {
        window.google.accounts.id.initialize({
          client_id: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
          callback: handleGoogleResponse,
        });
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: "outline",
          size: "large",
          width: 320,
        });
        clearInterval(interval);
      }
    }, 100);

    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await apiFetch("/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email, password, full_name: fullName }),
      });

      const loginData = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      localStorage.setItem("access_token", loginData.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-black px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-semibold text-white mb-6 text-center">
          Create your ClipMind AI account
        </h1>

        <div className="flex justify-center mb-6">
          <div ref={googleButtonRef} />
        </div>

        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 h-px bg-neutral-800" />
          <span className="text-xs text-neutral-500">OR</span>
          <div className="flex-1 h-px bg-neutral-800" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-neutral-400 mb-1">Full name</label>
            <input
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
            />
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
            />
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
            />
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-white text-black font-medium py-2.5 hover:bg-neutral-200 transition disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Sign up"}
          </button>
        </form>

        <p className="text-sm text-neutral-500 text-center mt-6">
          Already have an account?{" "}
          <a href="/login" className="text-white underline">
            Log in
          </a>
        </p>
      </div>
    </div>
  );
}