import Link from 'next/link';
import { ArrowLeft, Server, Cloud, Container } from 'lucide-react';

const deploymentOptions = [
  { name: 'Docker Compose', icon: Container, description: 'Single-node deployment for development and small teams', status: 'Available' },
  { name: 'Kubernetes', icon: Server, description: 'Production-grade deployment with auto-scaling', status: 'Available' },
  { name: 'Managed Cloud', icon: Cloud, description: 'One-click deployment on AWS, GCP, or Azure', status: 'Coming Soon' },
];

export default function DeployPage() {
  return (
    <div className="min-h-screen bg-zinc-950 pt-24 pb-16">
      <div className="mx-auto max-w-4xl px-6">
        <Link href="/docs" className="inline-flex items-center gap-2 text-sm text-zinc-400 hover:text-zinc-50 mb-8">
          <ArrowLeft className="h-4 w-4" /> Back to Docs
        </Link>

        <h1 className="text-4xl font-bold text-zinc-50 mb-4">Deployment</h1>
        <p className="text-lg text-zinc-400 mb-12">Deploy Open Forge on your infrastructure, your way.</p>

        <div className="space-y-4 mb-12">
          {deploymentOptions.map((option) => {
            const Icon = option.icon;
            return (
              <div key={option.name} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <Icon className="h-8 w-8 text-violet-500 mt-1" />
                    <div>
                      <h2 className="text-xl font-semibold text-zinc-50">{option.name}</h2>
                      <p className="text-zinc-400 mt-1">{option.description}</p>
                    </div>
                  </div>
                  <span className={`rounded-full px-3 py-1 text-xs ${option.status === 'Available' ? 'bg-green-500/20 text-green-400' : 'bg-zinc-700 text-zinc-400'}`}>
                    {option.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-6">
          <p className="text-zinc-300">
            <strong className="text-violet-400">Coming Soon:</strong> Helm charts and Terraform modules.
          </p>
        </div>
      </div>
    </div>
  );
}
