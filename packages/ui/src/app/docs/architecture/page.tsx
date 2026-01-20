import Link from 'next/link';
import { ArrowLeft, Layers } from 'lucide-react';

const layers = [
  { name: 'UI Portal', tech: 'React / Next.js', description: 'Modern web interface for platform management' },
  { name: 'API Gateway', tech: 'FastAPI + GraphQL', description: 'Unified API layer with real-time streaming' },
  { name: 'Agent Clusters', tech: '6 Specialized Clusters', description: 'Discovery, Architect, Builder, Operations, Enablement, Orchestration' },
  { name: 'Agent Framework', tech: 'LangGraph', description: 'Stateful, multi-actor agent orchestration' },
  { name: 'Core Engines', tech: 'Ontology + Codegen + Pipeline', description: 'The brains of the platform' },
  { name: 'Connectors', tech: '50+ Data Sources', description: 'PostgreSQL, S3, REST, GraphQL, and more' },
];

export default function ArchitecturePage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <Link href="/docs" className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-50 mb-8">
          <ArrowLeft className="h-4 w-4" /> Back to Docs
        </Link>

        <div className="flex items-center gap-3 mb-4">
          <Layers className="h-8 w-8 text-violet-500" />
          <h1 className="text-4xl font-bold text-zinc-50">Architecture</h1>
        </div>
        <p className="text-lg text-zinc-400 mb-12">A deep dive into Open Forge's layered architecture.</p>

        <div className="space-y-4 mb-12">
          {layers.map((layer) => (
            <div key={layer.name} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="text-xl font-semibold text-zinc-50">{layer.name}</h3>
                  <p className="text-sm text-zinc-400 mt-1">{layer.description}</p>
                </div>
                <span className="rounded-full bg-violet-500/20 px-3 py-1 text-xs text-violet-400 whitespace-nowrap">
                  {layer.tech}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-6">
          <p className="text-zinc-300">
            <strong className="text-violet-400">Coming Soon:</strong> Interactive architecture diagrams and deep-dives.
          </p>
        </div>
      </div>
    </div>
  );
}
