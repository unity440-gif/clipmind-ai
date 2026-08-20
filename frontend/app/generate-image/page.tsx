"use client";

import { useState } from "react";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import AppNav from "@/app/components/AppNav";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function GenerateImagePage() {
  const [prompt, setPrompt] = useState("");
  const [aspectRatio, setAspectRatio] = useState("1:1");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setImageUrl(null);

    try {
      const token = getToken();
      const data = await apiFetch("/images/generate", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ prompt, aspect_ratio: aspectRatio }),
      });
      setImageUrl(`${API_URL}${data.url}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Image generation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#0A0F1A] text-white">
      <AppNav />

      <main className="max-w-[480px] mx-auto px-6 pt-16 pb-16">
        <p className="text-[19px] text-[#F4F6F8] mb-1">Generate an image</p>
        <p className="text-[12px] text-[#6E7A8C] mb-8">
          Describe what you want. Costs 1 credit per image.
        </p>

        <form onSubmit={handleGenerate} className="space-y-4 mb-8">
          <div>
            <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Prompt</label>
            <textarea
              required
              rows={3}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="e.g. A cozy coffee shop interior at sunset, warm lighting, cinematic"
              className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[14px] px-3.5 py-2.5 outline-none focus:border-[#3B7DD8] transition resize-none"
            />
          </div>

          <div>
            <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Aspect ratio</label>
            <div className="flex gap-2">
              {["1:1", "16:9", "9:16"].map((ratio) => (
                <button
                  key={ratio}
                  type="button"
                  onClick={() => setAspectRatio(ratio)}
                  className={`text-[12px] px-3.5 py-1.5 rounded-lg border transition ${
                    aspectRatio === ratio
                      ? "bg-[#141F30] text-[#8FBBF0] border-[#3B7DD8]"
                      : "text-[#9AA7B8] border-[#22304A] hover:border-[#2A3B52]"
                  }`}
                >
                  {ratio}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <p className="text-[13px] text-[#D98787] bg-[#2A1616]/60 border border-[#4A2222] rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-[#3B7DD8] text-white text-[13px] font-medium px-5 py-2.5 hover:bg-[#4A8AE0] transition disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate image (1 credit)"}
          </button>
        </form>

        {imageUrl ? (
          <div className="rounded-xl border border-[#1A2434] overflow-hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imageUrl} alt={prompt} className="w-full" />
          </div>
        ) : (
          <div className="rounded-xl border border-[#1A2434] bg-[#0F1622] aspect-square flex items-center justify-center">
            <p className="text-[11px] text-[#4A5568]">Your image will appear here</p>
          </div>
        )}
      </main>
    </div>
  );
}