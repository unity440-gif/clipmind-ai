"use client";

import { useState } from "react";
import { getToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import AppNav from "@/app/components/AppNav";

const VOICE_OPTIONS = [
  { value: "adrian", label: "Adrian (M)" },
  { value: "laura", label: "Laura (F)" },
  { value: "ethan", label: "Ethan (M)" },
  { value: "male-child", label: "Male child" },
  { value: "female-child", label: "Female child" },
  { value: "story-narrator", label: "Story narrator" },
];

export default function TextToSpeechPage() {
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
    <div className="min-h-screen bg-[#0A0F1A] text-white">
      <AppNav />

      <main className="max-w-[480px] mx-auto px-6 pt-16 pb-16">
        <p className="text-[19px] text-[#F4F6F8] mb-1">Text to speech</p>
        <p className="text-[12px] text-[#6E7A8C] mb-8">
          Type text, pick a voice. Costs 1 credit per generation.
        </p>

        <form onSubmit={handleGenerate} className="space-y-4 mb-8">
          <div>
            <label className="block text-[12px] text-[#9AA7B8] mb-1.5">Text</label>
            <textarea
              required
              rows={4}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Type what you want spoken aloud..."
              className="w-full rounded-lg bg-[#0F1622] border border-[#22304A] text-white text-[14px] px-3.5 py-2.5 outline-none focus:border-[#3B7DD8] transition resize-none"
            />
          </div>

          <div>
            <label className="block text-[12px] text-[#9AA7B8] mb-2">Narrator voice</label>
            <div className="grid grid-cols-3 gap-2">
              {VOICE_OPTIONS.map((v) => (
                <button
                  key={v.value}
                  type="button"
                  onClick={() => setVoice(v.value)}
                  className={`text-[11px] py-2 rounded-lg border transition ${
                    voice === v.value
                      ? "bg-[#141F30] text-[#8FBBF0] border-[#3B7DD8]"
                      : "text-[#9AA7B8] border-[#22304A] hover:border-[#2A3B52]"
                  }`}
                >
                  {v.label}
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
            {loading ? "Generating..." : "Generate speech (1 credit)"}
          </button>
        </form>

        {audioUrl && (
          <div className="rounded-xl border border-[#1A2434] bg-[#0F1622] p-4">
            <audio controls className="w-full" src={audioUrl} />
          </div>
        )}
      </main>
    </div>
  );
}