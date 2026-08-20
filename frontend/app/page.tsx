"use client";

import Link from "next/link";
import { useState } from "react";

export default function HomePage() {
  const [openMenu, setOpenMenu] = useState<string | null>(null);

  const menus: Record<string, { label: string; desc: string }[]> = {
    Features: [
      { label: "AI hook detection", desc: "Finds the moments worth sharing" },
      { label: "Auto captions", desc: "Synced, styled, and editable" },
      { label: "YouTube import", desc: "Paste a link, no download needed" },
      { label: "Multiple formats", desc: "16:9, 9:16, or 1:1 in one click" },
      { label: "Photo generation", desc: "Create images from a text prompt" },
      { label: "Text to speech", desc: "Six real narrator voices for any script" },
      { label: "Script to video", desc: "Turn a script into scenes, no footage needed" },
      { label: "Quick reformat", desc: "Change a video's aspect ratio, nothing else" },
      { label: "Generation history", desc: "Every image and voiceover you've made" },
    ],
    Pricing: [
      { label: "Pay as you go", desc: "Credits, no subscription required" },
      { label: "Buy credits", desc: "Top up anytime from your billing page" },
    ],
    Docs: [
      { label: "Getting started", desc: "Upload your first video in minutes" },
      { label: "API reference", desc: "Coming soon" },
    ],
  };

  return (
    <div
      className="min-h-screen text-white bg-cover bg-center bg-fixed relative"
      style={{ backgroundImage: "url('/bg-home.jpg')" }}
    >
      <div className="fixed inset-0 bg-black/50 pointer-events-none" />
      <div className="relative z-10">
        <header className="border-b border-white/10 px-6 py-5 flex items-center justify-between max-w-6xl mx-auto relative">
          <div className="flex items-center gap-10">
            <img src="/logo.png" alt="ClipMind AI" className="h-12 w-auto" />
            <nav className="hidden sm:flex items-center gap-7 text-[13px] text-white/70">
              {Object.keys(menus).map((menu) => (
                <div
                  key={menu}
                  className="relative"
                  onMouseEnter={() => setOpenMenu(menu)}
                  onMouseLeave={() => setOpenMenu(null)}
                >
                  <span className="hover:text-white transition cursor-pointer py-2 block">
                    {menu}
                  </span>
                  {openMenu === menu && (
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-72 max-h-[70vh] overflow-y-auto bg-black/90 backdrop-blur-md border border-white/15 rounded-xl p-2 shadow-xl">
                      {menus[menu].map((item) => (
                        <div
                          key={item.label}
                          className="px-3 py-2.5 rounded-lg hover:bg-white/10 transition cursor-pointer"
                        >
                          <p className="text-[13px] text-white">{item.label}</p>
                          <p className="text-[11px] text-white/50 mt-0.5">{item.desc}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </nav>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/login" className="text-[13px] text-white/80 hover:text-white transition">
              Sign in
            </Link>
            <Link
              href="/signup"
              className="bg-white text-[#0A0A0D] text-[12px] font-medium px-4 py-2 rounded-md hover:bg-white/90 transition"
            >
              Get started
            </Link>
          </div>
        </header>

        <section className="max-w-[540px] mx-auto px-6 pt-24 pb-16 text-center">
          <p className="text-[14px] text-white/85 mb-4 tracking-wide font-medium">
            New: turn a script into a video, no footage needed
          </p>
          <h1 className="text-[38px] leading-[1.15] tracking-[-0.5px] font-normal text-white mb-4">
            Your best 60 seconds,
            <br />
            found automatically
          </h1>
          <p className="text-[15px] leading-[1.6] text-white/80 mb-8">
            Upload a video or paste a YouTube link. ClipMind reads the full
            transcript, finds the moments a stranger would actually stop
            scrolling for, and hands you clips ready to post.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link
              href="/signup"
              className="bg-[#3B7DD8] text-white text-[13px] font-medium px-5 py-2.5 rounded-md hover:bg-[#4A8AE0] transition"
            >
              Start clipping — free
            </Link>
          </div>
        </section>

        <section className="max-w-[720px] mx-auto px-6 py-16 border-t border-white/10 bg-black/30">
          <h2 className="text-[13px] text-white/70 text-center mb-14 tracking-wide">
            FROM VIDEO TO VIRAL IN THREE STEPS
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-10">
            <div>
              <div className="text-[11px] text-white/50 mb-3 font-mono">01</div>
              <h3 className="text-[14px] text-white mb-2">Upload or paste a link</h3>
              <p className="text-[12px] text-white/70 leading-[1.6]">
                Drop in an MP4, MOV, AVI, or MKV — or just paste a YouTube URL.
                Long-form, podcasts, interviews, all of it works.
              </p>
            </div>
            <div>
              <div className="text-[11px] text-white/50 mb-3 font-mono">02</div>
              <h3 className="text-[14px] text-white mb-2">AI finds the best clips</h3>
              <p className="text-[12px] text-white/70 leading-[1.6]">
                ClipMind reads the full transcript and ranks the moments most
                likely to hold someone's attention.
              </p>
            </div>
            <div>
              <div className="text-[11px] text-white/50 mb-3 font-mono">03</div>
              <h3 className="text-[14px] text-white mb-2">Get ready-to-post clips</h3>
              <p className="text-[12px] text-white/70 leading-[1.6]">
                Each clip comes captioned, scored, and written up with
                platform-specific captions and hashtags.
              </p>
            </div>
          </div>
        </section>

        <section className="max-w-[640px] mx-auto px-6 py-16">
          <div className="bg-black/50 backdrop-blur-md border border-white/15 rounded-[10px] overflow-hidden">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-white/15">
              <div className="w-[7px] h-[7px] rounded-full bg-white/30" />
              <div className="w-[7px] h-[7px] rounded-full bg-white/30" />
              <div className="w-[7px] h-[7px] rounded-full bg-white/30" />
              <span className="text-[11px] text-white/60 ml-2">clipmind.ai/dashboard</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3">
              <div className="p-5 border-b sm:border-b-0 sm:border-r border-white/15">
                <p className="text-[10px] text-white/60 mb-3.5">YOUR PROJECTS</p>
                <div className="text-[12px] text-white mb-2.5">Podcast ep. 12</div>
                <div className="text-[12px] text-white/70 mb-2.5">Interview cut</div>
                <div className="text-[12px] text-white/70">Keynote 2026</div>
              </div>
              <div className="p-5 sm:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[12px] text-white">Clip 2 of 5</span>
                  <span className="text-[11px] text-[#8FBBF0] bg-[#1C2E48] px-2.5 py-1 rounded">
                    99 · likely to hook viewers
                  </span>
                </div>
                <div className="h-20 bg-black/50 border border-white/15 rounded-lg flex items-center justify-center mb-3.5">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#8FBBF0" strokeWidth="2">
                    <polygon points="6 3 20 12 6 21 6 3" />
                  </svg>
                </div>
                <div className="h-[3px] bg-white/15 rounded-full overflow-hidden mb-2">
                  <div className="w-[64%] h-full bg-[#3B7DD8]" />
                </div>
                <p className="text-[11px] text-white/60">Rendering — captions burning in now</p>
              </div>
            </div>
          </div>
        </section>

        <section className="max-w-[720px] mx-auto px-6 py-16 border-t border-white/10 bg-black/30">
          <h2 className="text-[13px] text-white/70 text-center mb-14 tracking-wide">
            EVERYTHING YOU NEED TO CLIP LIKE A PRO
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-10">
            {[
              { title: "AI hook detection", desc: "Finds the moments with the strongest hooks, emotion, and story arcs." },
              { title: "Virality scoring", desc: "Every clip is ranked by predicted performance, so you know what to post first." },
              { title: "Auto captions & hashtags", desc: "Platform-specific captions and hashtags generated for every clip." },
              { title: "YouTube import", desc: "No download needed — just paste a link and we handle the rest." },
              { title: "Fast rendering", desc: "Clips are cut and ready to preview in your dashboard within moments." },
              { title: "Multiple formats", desc: "Export in 16:9, 9:16, or 1:1 to fit any platform." },
            ].map((feature) => (
              <div key={feature.title}>
                <p className="text-[13px] text-white mb-1.5">{feature.title}</p>
                <p className="text-[12px] text-white/70 leading-[1.6]">{feature.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="max-w-[480px] mx-auto px-6 py-24 text-center">
          <h2 className="text-[24px] font-normal text-white mb-3 tracking-[-0.3px]">
            Ready to go viral?
          </h2>
          <p className="text-[14px] text-white/80 mb-8">
            Create your first clip in minutes — no credit card required.
          </p>
          <Link
            href="/signup"
            className="inline-block bg-[#3B7DD8] text-white text-[13px] font-medium px-6 py-3 rounded-md hover:bg-[#4A8AE0] transition"
          >
            Get started free
          </Link>
        </section>

        <footer className="border-t border-white/10 py-8 text-center text-[12px] text-white/60 bg-black/30">
          © 2026 ClipMind AI. All rights reserved.
        </footer>
      </div>
    </div>
  );
}