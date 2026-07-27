import Link from "next/link";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Nav */}
      <header className="border-b border-neutral-900 px-6 py-4 flex items-center justify-between max-w-6xl mx-auto">
        <span className="text-lg font-semibold">ClipMind AI</span>
        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-sm text-neutral-400 hover:text-white transition"
          >
            Log in
          </Link>
          <Link
            href="/signup"
            className="rounded-lg bg-white text-black text-sm font-medium px-4 py-2 hover:bg-neutral-200 transition"
          >
            Get Started
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-24 pb-20 text-center">
        <h1 className="text-4xl sm:text-6xl font-semibold tracking-tight leading-tight">
          Turn long videos into
          <br />
          <span className="bg-gradient-to-r from-white to-neutral-500 bg-clip-text text-transparent">
            viral short clips
          </span>
        </h1>
        <p className="mt-6 text-lg text-neutral-400 max-w-xl mx-auto">
          Upload a video or paste a YouTube link. Our AI finds the best moments,
          writes the hooks and captions, and cuts the clips — automatically.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link
            href="/signup"
            className="rounded-lg bg-white text-black font-medium px-6 py-3 hover:bg-neutral-200 transition"
          >
            Start Clipping — Free
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-t border-neutral-900">
        <h2 className="text-2xl sm:text-3xl font-semibold text-center mb-16">
          From video to viral in three steps
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-10">
          <div>
            <div className="text-sm text-neutral-600 mb-2">01</div>
            <h3 className="text-lg font-medium mb-2">Upload or paste a link</h3>
            <p className="text-neutral-400 text-sm">
              Drop in an MP4, MOV, AVI, or MKV — or just paste a YouTube URL.
              Long-form, podcasts, interviews, anything works.
            </p>
          </div>
          <div>
            <div className="text-sm text-neutral-600 mb-2">02</div>
            <h3 className="text-lg font-medium mb-2">AI finds the best clips</h3>
            <p className="text-neutral-400 text-sm">
              Our AI analyzes the full transcript and identifies the moments
              most likely to hook viewers and hold their attention.
            </p>
          </div>
          <div>
            <div className="text-sm text-neutral-600 mb-2">03</div>
            <h3 className="text-lg font-medium mb-2">Get ready-to-post clips</h3>
            <p className="text-neutral-400 text-sm">
              Each clip comes with a title, hook, and platform-specific
              captions and hashtags for TikTok, Reels, and Shorts.
            </p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-t border-neutral-900">
        <h2 className="text-2xl sm:text-3xl font-semibold text-center mb-16">
          Everything you need to clip like a pro
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              title: "AI Hook Detection",
              desc: "Finds the moments with the strongest hooks, emotion, and story arcs.",
            },
            {
              title: "Virality Scoring",
              desc: "Every clip is ranked by predicted performance, so you know what to post first.",
            },
            {
              title: "Auto Captions & Hashtags",
              desc: "Platform-specific captions and hashtags generated for every clip.",
            },
            {
              title: "YouTube Import",
              desc: "No download needed — just paste a link and we handle the rest.",
            },
            {
              title: "Fast Rendering",
              desc: "Clips are cut and ready to preview in your dashboard within moments.",
            },
            {
              title: "Multiple Formats",
              desc: "Export in 16:9, 9:16, or 1:1 to fit any platform.",
            },
          ].map((feature) => (
            <div
              key={feature.title}
              className="rounded-xl border border-neutral-900 bg-neutral-950 p-6"
            >
              <h3 className="font-medium mb-2">{feature.title}</h3>
              <p className="text-sm text-neutral-400">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-3xl mx-auto px-6 py-24 text-center border-t border-neutral-900">
        <h2 className="text-3xl font-semibold mb-4">Ready to go viral?</h2>
        <p className="text-neutral-400 mb-8">
          Create your first clip in minutes — no credit card required.
        </p>
        <Link
          href="/signup"
          className="rounded-lg bg-white text-black font-medium px-6 py-3 hover:bg-neutral-200 transition inline-block"
        >
          Get Started Free
        </Link>
      </section>

      {/* Footer */}
      <footer className="border-t border-neutral-900 py-8 text-center text-sm text-neutral-600">
        © 2026 ClipMind AI. All rights reserved.
      </footer>
    </div>
  );
}