"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";

const VOICE_OPTIONS = [
  { value: "adrian", label: "Adrian (Male)" },
  { value: "laura", label: "Laura (Female)" },
  { value: "ethan", label: "Ethan (Male)" },
  { value: "male-child", label: "Male Child" },
  { value: "female-child", label: "Female Child" },
  { value: "story-narrator", label: "Story Narrator" },
];

export default function TextToSpeechPage() {
  const router = useRouter();
  const [text, setText] = useState("");
  const [voice, setVoice] = useState("adrian");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    setAudioUrl(null);

    try {
      const token = getToken();
      const data = await apiFetch("/tts/generate", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ text, voice }),
      });
      setAudioUrl(data.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Speech generation failed.");
    } finally {
      setLoading(false);
    }
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

      <main className="max-w-2xl mx-auto px-6 py-10">
        <h1 className="text-2xl font-semibold mb-2">Text to Speech</h1>
        <p className="text-neutral-500 text-sm mb-8">
          Type text and generate real speech audio. Costs 1 credit per generation.
        </p>

        <form onSubmit={handleGenerate} className="space-y-4 mb-8">
          <div>
            <label className="block text-sm text-neutral-400 mb-1">Text</label>
            <textarea
              required
              rows={4}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type what you want spoken aloud..."
              className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600 resize-none"
            />
          </div>

          <div>
            <label className="block text-sm text-neutral-400 mb-1">Narrator voice</label>
            <select
              value={voice}
              onChange={(e) => setVoice(e.target.value)}
              className="w-full rounded-lg bg-neutral-900 border border-neutral-800 text-white px-4 py-2.5 outline-none focus:border-neutral-600"
            >
              {VOICE_OPTIONS.map((v) => (
                <option key={v.value} value={v.value}>
                  {v.label}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-950/40 border border-red-900 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-white text-black text-sm font-medium px-5 py-2.5 hover:bg-neutral-200 transition disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Speech (1 credit)"}
          </button>
        </form>

        {audioUrl && (
          <div className="rounded-xl border border-neutral-800 bg-neutral-950 p-5">
            <audio controls className="w-full" src={audioUrl} />
          </div>
        )}
      </main>
    </div>
  );
}