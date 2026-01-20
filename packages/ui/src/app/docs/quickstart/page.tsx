import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function QuickStartPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-3xl px-6">
        <Link href="/docs" className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-50 mb-8">
          <ArrowLeft className="h-4 w-4" /> Back to Docs
        </Link>

        <h1 className="text-4xl font-bold text-zinc-50 mb-4">Quick Start</h1>
        <p className="text-lg text-zinc-400 mb-8">Get Open Forge running in under 5 minutes.</p>

        <div className="space-y-8">
          <section>
            <h2 className="text-2xl font-semibold text-zinc-50 mb-4">1. Clone the Repository</h2>
            <div className="rounded-lg bg-zinc-900 border border-zinc-800 p-4 font-mono text-sm text-zinc-300">
              <code>git clone https://github.com/overlordai/open-forge.git</code>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-zinc-50 mb-4">2. Install Dependencies</h2>
            <div className="rounded-lg bg-zinc-900 border border-zinc-800 p-4 font-mono text-sm text-zinc-300">
              <code>cd open-forge && npm install</code>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-zinc-50 mb-4">3. Configure Environment</h2>
            <div className="rounded-lg bg-zinc-900 border border-zinc-800 p-4 font-mono text-sm text-zinc-300">
              <code>cp .env.example .env.local</code>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-zinc-50 mb-4">4. Start the Platform</h2>
            <div className="rounded-lg bg-zinc-900 border border-zinc-800 p-4 font-mono text-sm text-zinc-300">
              <code>docker-compose up -d</code>
            </div>
          </section>

          <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-6">
            <p className="text-zinc-300">
              <strong className="text-violet-400">Coming Soon:</strong> Detailed setup guides and video walkthroughs.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
