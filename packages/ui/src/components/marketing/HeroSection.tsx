import Link from 'next/link';
import Image from 'next/image';
import { Github, ArrowRight, Rocket } from 'lucide-react';

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-20">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-violet-950/20 via-zinc-950 to-zinc-950" />

      {/* Animated grid background */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgb(139 92 246 / 0.1) 1px, transparent 1px),
            linear-gradient(to bottom, rgb(139 92 246 / 0.1) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Large background logo watermark */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <Image
          src="/open_forge.png"
          alt=""
          width={800}
          height={800}
          className="w-[500px] h-[500px] sm:w-[600px] sm:h-[600px] lg:w-[800px] lg:h-[800px] opacity-20"
          priority
        />
      </div>

      <div className="relative z-10 mx-auto max-w-5xl px-6 text-center">
        {/* Badge */}
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-sm text-violet-300">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-violet-400 opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-violet-500" />
          </span>
          20+ Autonomous Agents | 6 Agent Clusters | Apache 2.0 Licensed
        </div>

        {/* Headline */}
        <h1 className="mb-6 text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
          <span className="text-zinc-50">The </span>
          <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-violet-400 bg-clip-text text-transparent">
            Open Source
          </span>
          <br />
          <span className="text-zinc-50">Ontology Platform</span>
        </h1>

        {/* Subheadline */}
        <p className="mx-auto mb-8 max-w-2xl text-lg text-zinc-400 sm:text-xl">
          Enterprise-grade data infrastructure with autonomous AI agents.{' '}
          <span className="text-zinc-200">No consultants required.</span>{' '}
          <span className="text-zinc-200">No vendor lock-in.</span>{' '}
          Your ontology, your operations, your code.
        </p>

        {/* Value proposition */}
        <p className="mx-auto mb-12 max-w-xl text-base text-zinc-500">
          Why pay millions for proprietary platforms and forward-deployed engineers when
          autonomous agents can build, integrate, and operate your data infrastructure 24/7?
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="https://github.com/overlordai/open-forge"
            target="_blank"
            rel="noopener noreferrer"
            className="group flex items-center gap-2 rounded-lg bg-violet-600 px-6 py-3 text-base font-semibold text-white hover:bg-violet-500 transition-colors"
          >
            <Github className="h-5 w-5" />
            Star on GitHub
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="#get-started"
            className="flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800/50 px-6 py-3 text-base font-semibold text-zinc-50 hover:bg-zinc-800 transition-colors"
          >
            <Rocket className="h-5 w-5" />
            Deploy Now
          </Link>
          <Link
            href="#contact"
            className="flex items-center gap-2 rounded-lg border border-zinc-800 px-6 py-3 text-base font-semibold text-zinc-400 hover:text-zinc-50 hover:border-zinc-700 transition-colors"
          >
            Request Demo
          </Link>
        </div>

        {/* Social proof strip */}
        <div className="mt-16 flex flex-wrap items-center justify-center gap-8 text-sm text-zinc-500">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-green-500" />
            <span>10 Packages</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-violet-500" />
            <span>20+ Agents</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-blue-500" />
            <span>50+ API Endpoints</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-purple-500" />
            <span>4 Code Generators</span>
          </div>
        </div>
      </div>
    </section>
  );
}
