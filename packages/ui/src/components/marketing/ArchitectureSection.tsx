import { ExternalLink } from 'lucide-react';

const layers = [
  { name: 'UI Portal', tech: 'React / Next.js', color: 'bg-violet-500' },
  { name: 'API Gateway', tech: 'FastAPI + GraphQL + SSE', color: 'bg-purple-500' },
  {
    name: 'Agent Clusters',
    items: ['Discovery', 'Data Architect', 'App Builder', 'Operations'],
    color: 'bg-indigo-500'
  },
  { name: 'Agent Framework', tech: 'LangGraph', color: 'bg-blue-500' },
  {
    name: 'Core Engines',
    items: ['Ontology Engine', 'Codegen Engine', 'Pipeline Engine'],
    color: 'bg-cyan-500'
  },
  { name: 'Connectors', tech: 'PostgreSQL, S3, REST, GraphQL...', color: 'bg-teal-500' },
];

const stats = [
  { label: '10 Packages', value: '10' },
  { label: '20+ Agents', value: '20+' },
  { label: '50+ Endpoints', value: '50+' },
  { label: '7 Connectors', value: '7' },
  { label: '4 Generators', value: '4' },
];

export function ArchitectureSection() {
  return (
    <section className="relative py-24" id="architecture">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-bold text-zinc-50 sm:text-5xl">
            Full Stack.{' '}
            <span className="bg-gradient-to-r from-violet-400 to-purple-400 bg-clip-text text-transparent">
              Open Source.
            </span>{' '}
            Production Ready.
          </h2>
        </div>

        <div className="mb-12 rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6 md:p-8">
          <div className="space-y-3">
            {layers.map((layer, index) => (
              <div
                key={layer.name}
                className="group relative overflow-hidden rounded-lg border border-zinc-700 bg-zinc-800/50 p-4 transition-all hover:border-violet-500/50"
              >
                <div className={`absolute left-0 top-0 bottom-0 w-1 ${layer.color}`} />

                <div className="ml-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <span className="font-semibold text-zinc-50">{layer.name}</span>
                  {'tech' in layer && (
                    <span className="text-sm text-zinc-500">{layer.tech}</span>
                  )}
                  {'items' in layer && layer.items && (
                    <div className="flex flex-wrap gap-2">
                      {layer.items.map((item) => (
                        <span
                          key={item}
                          className="rounded-full bg-zinc-700/50 px-3 py-1 text-xs text-zinc-300"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {index < layers.length - 1 && (
                  <div className="absolute left-6 -bottom-3 h-3 w-px bg-zinc-700" />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="mb-8 flex flex-wrap justify-center gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl font-bold text-violet-400">{stat.value}</div>
              <div className="text-sm text-zinc-500">{stat.label}</div>
            </div>
          ))}
        </div>

        <div className="text-center">
          <a
            href="/docs/architecture"
            className="inline-flex items-center gap-2 text-violet-400 hover:text-violet-300 transition-colors"
          >
            Explore the Full Architecture
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </div>
    </section>
  );
}
