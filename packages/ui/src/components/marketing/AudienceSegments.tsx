'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Code2, Building2, Crown, Github, FileText, Rocket, Users, BarChart3, Mail } from 'lucide-react';
import { cn } from '@/lib/utils';

type AudienceKey = 'engineers' | 'leaders' | 'executives';

interface AudienceData {
  key: AudienceKey;
  icon: React.ElementType;
  label: string;
  headline: string;
  body: string[];
  ctas: { label: string; href: string; icon: React.ElementType; primary?: boolean }[];
}

const audiences: AudienceData[] = [
  {
    key: 'engineers',
    icon: Code2,
    label: 'For Engineers',
    headline: 'Own the Code That Runs the World',
    body: [
      'The platforms that power Fortune 500 data operations shouldn\'t be proprietary black boxes. Open Forge is the ontology platform built in the open—Python, TypeScript, LangGraph, FastAPI, React—modern stack, MIT-educated architecture, Apache 2.0 licensed.',
      'This isn\'t a toy. It\'s 80,000+ lines of production code across 10 packages: ontology compilers, connector frameworks, pipeline engines, agent orchestration, human-in-the-loop workflows, and full-stack code generation.',
      'The proprietary platforms had a 20-year head start. We have a community.',
    ],
    ctas: [
      { label: 'Star on GitHub', href: 'https://github.com/overlordai/open-forge', icon: Github, primary: true },
      { label: 'Read the Architecture', href: '/docs/architecture', icon: FileText },
      { label: 'First Good Issues', href: 'https://github.com/overlordai/open-forge/issues?q=is:issue+is:open+label:"good+first+issue"', icon: Code2 },
    ],
  },
  {
    key: 'leaders',
    icon: Building2,
    label: 'For Technical Leaders',
    headline: 'Your Data Platform. Your Rules.',
    body: [
      'Stop renting your data infrastructure. Open Forge deploys on your cloud, your Kubernetes cluster, your terms. Connect to PostgreSQL, MySQL, S3, REST APIs, GraphQL endpoints—50+ connector types with schema discovery built in.',
      'The ontology layer you define is portable. The pipelines are Dagster-native. The APIs are standard REST and GraphQL. When you need to change direction, you change direction—no exit negotiations, no migration fees, no hostage situations.',
    ],
    ctas: [
      { label: 'Deploy on Your Infrastructure', href: '/docs/deploy', icon: Rocket, primary: true },
      { label: 'View Connectors', href: '/docs/connectors', icon: Users },
      { label: 'Book Architecture Review', href: '/contact?type=architecture', icon: Building2 },
    ],
  },
  {
    key: 'executives',
    icon: Crown,
    label: 'For Executives',
    headline: 'AI Transformation Without the Tribute',
    body: [
      'Your competitors are spending $10M+ annually on proprietary platforms and armies of consultants. You can deploy the same ontology-powered, AI-operated infrastructure—and own it outright.',
      'Open Forge\'s autonomous agents replace the forward-deployed engineer model entirely. Discovery agents interview stakeholders. Architect agents design schemas. Builder agents generate applications. Operations agents monitor and scale. 24/7, no billable hours.',
      'This is AI enablement without indentured servitude.',
    ],
    ctas: [
      { label: 'Request Executive Briefing', href: '/contact?type=executive', icon: Mail, primary: true },
      { label: 'View ROI Calculator', href: '/roi', icon: BarChart3 },
      { label: 'Compare to Alternatives', href: '/compare', icon: FileText },
    ],
  },
];

export function AudienceSegments() {
  const [activeTab, setActiveTab] = useState<AudienceKey>('engineers');
  const activeAudience = audiences.find((a) => a.key === activeTab)!;

  return (
    <section className="relative py-24 bg-zinc-900/50" id="audiences">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-4xl font-bold text-zinc-50 sm:text-5xl">
            Built For Everyone Who's Had Enough
          </h2>
        </div>

        <div className="mb-8 flex justify-center">
          <div className="inline-flex rounded-lg border border-zinc-800 bg-zinc-900 p-1">
            {audiences.map((audience) => {
              const Icon = audience.icon;
              return (
                <button
                  key={audience.key}
                  onClick={() => setActiveTab(audience.key)}
                  className={cn(
                    'flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors',
                    activeTab === audience.key
                      ? 'bg-violet-600 text-white'
                      : 'text-zinc-400 hover:text-zinc-50'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span className="hidden sm:inline">{audience.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-zinc-800 bg-zinc-950 p-8 md:p-12">
          <h3 className="mb-6 text-3xl font-bold text-zinc-50">
            {activeAudience.headline}
          </h3>

          <div className="mb-8 space-y-4">
            {activeAudience.body.map((paragraph, i) => (
              <p key={i} className="text-lg text-zinc-400 leading-relaxed">
                {paragraph}
              </p>
            ))}
          </div>

          <div className="flex flex-wrap gap-4">
            {activeAudience.ctas.map((cta) => {
              const Icon = cta.icon;
              return (
                <Link
                  key={cta.label}
                  href={cta.href}
                  target={cta.href.startsWith('http') ? '_blank' : undefined}
                  rel={cta.href.startsWith('http') ? 'noopener noreferrer' : undefined}
                  className={cn(
                    'flex items-center gap-2 rounded-lg px-5 py-2.5 text-sm font-medium transition-colors',
                    cta.primary
                      ? 'bg-violet-600 text-white hover:bg-violet-500'
                      : 'border border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-50'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {cta.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
