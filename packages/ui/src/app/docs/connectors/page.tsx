import Link from 'next/link';
import { ArrowLeft, Database, Cloud, Globe, FileJson } from 'lucide-react';

const connectorCategories = [
  { name: 'Databases', icon: Database, items: ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Neo4j'] },
  { name: 'Cloud Storage', icon: Cloud, items: ['AWS S3', 'Google Cloud Storage', 'Azure Blob', 'MinIO'] },
  { name: 'APIs', icon: Globe, items: ['REST', 'GraphQL', 'gRPC', 'WebSocket'] },
  { name: 'Files', icon: FileJson, items: ['CSV', 'Parquet', 'JSON', 'Excel', 'XML'] },
];

export default function ConnectorsPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <Link href="/docs" className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-50 mb-8">
          <ArrowLeft className="h-4 w-4" /> Back to Docs
        </Link>

        <h1 className="text-4xl font-bold text-zinc-50 mb-4">Connectors</h1>
        <p className="text-lg text-zinc-400 mb-12">Connect to 50+ data sources with automatic schema discovery.</p>

        <div className="grid gap-6 md:grid-cols-2">
          {connectorCategories.map((category) => {
            const Icon = category.icon;
            return (
              <div key={category.name} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <Icon className="h-6 w-6 text-violet-500" />
                  <h2 className="text-xl font-semibold text-zinc-50">{category.name}</h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {category.items.map((item) => (
                    <span key={item} className="rounded-full bg-zinc-800 px-3 py-1 text-sm text-zinc-300">{item}</span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-12 rounded-xl border border-violet-500/30 bg-violet-500/10 p-6">
          <p className="text-zinc-300">
            <strong className="text-violet-400">Coming Soon:</strong> Connector configuration guides and custom connector development.
          </p>
        </div>
      </div>
    </div>
  );
}
