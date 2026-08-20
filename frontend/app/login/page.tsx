"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

declare global {
  interface Window {
    google: any;
  }
}

export default function LoginPage() {
  const router = useRouter();
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
      setError(err instanceof Error ? err.message : "Google login failed.");
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
          theme: "filled_black",
          size: "large",
          width: 320,
          shape: "rectangular",
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
      const data = await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      localStorage.setItem("access_token", data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="min-h-screen relative flex items-center justify-center px-4 overflow-hidden bg-cover bg-center"
      style={{ backgroundImage: "url('/bg-login.jpg')" }}
    >
      <div className="absolute inset-0 bg-black/55" />
      <div className="relative z-10 w-full max-w-[380px] px-2 py-6">
        <Link href="/" className="flex justify-center mb-8">
          <img src="/logo.png" alt="ClipMind AI" className="h-10 w-auto" />
        </Link>

        <h1 className="text-[22px] font-normal text-white mb-1 text-center tracking-[-0.3px]">
          Welcome back
        </h1>
        <p className="text-[13px] text-white/70 text-center mb-8">
          Pick up where you left off
        </p>

        <div className="flex justify-center mb-6">
          <div ref={googleButtonRef} />
        </div>

        <div className="flex items-center gap-3 mb-6">
          <div className="flex-1 h-px bg-white/25" />
          <span className="text-[11px] text-white/60">OR</span>
          <div className="flex-1 h-px bg-white/25" />
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[12px] text-white/80 mb-1.5">Email address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl bg-black/30 border border-white/30 text-white text-[14px] px-4 py-3 outline-none focus:border-white/70 transition"
            />
          </div>

          <div>
            <label className="block text-[12px] text-white/80 mb-1.5">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl bg-black/30 border border-white/30 text-white text-[14px] px-4 py-3 outline-none focus:border-white/70 transition"
            />
          </div>

          {error && (
            <p className="text-[13px] text-white bg-[#7A2E2E]/80 border border-[#A44] rounded-xl px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-[#2D5A9B] text-white text-[14px] font-medium py-3 hover:bg-[#3468AC] transition disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>

        <p className="text-[13px] text-white/70 text-center mt-8">
          New to ClipMind?{" "}
          <Link href="/signup" className="text-white hover:underline transition font-medium">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}