import Link from 'next/link';
import { BookOpen, ArrowRight } from 'lucide-react';

const docSections = [
  { title: 'Quick Start', href: '/docs/quickstart', description: 'Get up and running in minutes' },
  { title: 'Architecture', href: '/docs/architecture', description: 'Understand the system design' },
  { title: 'Connectors', href: '/docs/connectors', description: 'Connect to your data sources' },
  { title: 'Deployment', href: '/docs/deploy', description: 'Deploy on your infrastructure' },
];

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <BookOpen className="h-8 w-8 text-violet-500" />
            <h1 className="text-4xl font-bold text-zinc-50">Documentation</h1>
          </div>
          <p className="text-lg text-zinc-400">
            Everything you need to build, deploy, and operate Open Forge.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {docSections.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              className="group rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 transition-all hover:border-violet-500/50 hover:bg-zinc-900"
            >
              <h2 className="mb-2 text-xl font-semibold text-zinc-50 group-hover:text-violet-400">
                {section.title}
              </h2>
              <p className="mb-4 text-sm text-zinc-400">{section.description}</p>
              <span className="inline-flex items-center gap-1 text-sm text-violet-400">
                Read more <ArrowRight className="h-4 w-4" />
              </span>
            </Link>
          ))}
        </div>

        <div className="mt-12 rounded-xl border border-zinc-800 bg-zinc-900/30 p-6 text-center">
          <p className="text-zinc-400">
            Full documentation coming soon. Check out our{' '}
            <a
              href="https://github.com/overlordai/open-forge"
              target="_blank"
              rel="noopener noreferrer"
              className="text-violet-400 hover:text-violet-300"
            >
              GitHub repository
            </a>{' '}
            for the latest updates.
          </p>
        </div>
      </div>
    </div>
  );
}
